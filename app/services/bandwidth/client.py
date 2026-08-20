from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

import httpx
import xml.etree.ElementTree as ET

from app.config import Settings
from .errors import BandwidthAPIError

logger = logging.getLogger("digicloud.bandwidth")


class BandwidthClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self.api_log: deque[dict[str, Any]] = deque(maxlen=settings.api_log_limit)

    async def _get_access_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token

        started = perf_counter()
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True) as client:
            response = await client.post(
                self.settings.bandwidth_token_url,
                data={"grant_type": "client_credentials"},
                auth=(self.settings.bandwidth_client_id, self.settings.bandwidth_client_secret),
                headers={"Accept": "application/json"},
            )
        latency = round((perf_counter() - started) * 1000)

        if response.is_error:
            payload = _safe_payload(response)
            raise BandwidthAPIError(
                f"OAuth token request failed with HTTP {response.status_code}.",
                response.status_code,
                payload,
                "POST",
                self.settings.bandwidth_token_url,
                latency,
            )

        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise BandwidthAPIError("OAuth response did not include access_token.", payload=payload)

        expires_in = max(int(payload.get("expires_in", 3600)) - 60, 60)
        self._access_token = token
        self._token_expires_at = now + timedelta(seconds=expires_in)
        return token

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        content: str | bytes | None = None,
        content_type: str = "application/json",
        accept: str = "application/json, application/xml, text/xml",
    ) -> Any:
        token = await self._get_access_token()
        url = path if path.startswith("http") else (
            f"{self.settings.bandwidth_api_base.rstrip('/')}/{path.lstrip('/')}"
        )
        started = perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True) as client:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    json=json_body if content is None else None,
                    content=content,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": accept,
                        "Content-Type": content_type,
                    },
                )
        except httpx.RequestError as exc:
            latency = round((perf_counter() - started) * 1000)
            self._record(method, url, None, latency, str(exc), params)
            raise BandwidthAPIError(
                f"Unable to reach Bandwidth: {exc}",
                method=method,
                url=url,
                latency_ms=latency,
            ) from exc

        latency = round((perf_counter() - started) * 1000)
        payload = _safe_payload(response)
        self._record(method, str(response.request.url), response.status_code, latency, payload, params)

        if response.is_error:
            message = _message(payload) or f"Bandwidth returned HTTP {response.status_code}."
            raise BandwidthAPIError(
                message,
                response.status_code,
                payload,
                method,
                str(response.request.url),
                latency,
            )

        if response.status_code == 204 or not response.content:
            return {}
        return payload

    def _record(self, method, url, status, latency, payload, params=None) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method.upper(),
            "url": url,
            "status": status,
            "latency_ms": latency,
            "params": params or {},
            "payload": payload,
        }
        self.api_log.appendleft(event)
        logger.info("%s %s -> %s (%sms)", method.upper(), url, status, latency)


def _safe_payload(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        text = response.text.strip()
        if text.startswith("<"):
            try:
                return _xml_to_dict(ET.fromstring(text))
            except ET.ParseError:
                pass
        return response.text


def _xml_to_dict(element: ET.Element) -> Any:
    """Convert XML into a natural nested dict without duplicate tag wrappers."""

    def convert(node: ET.Element) -> Any:
        children = list(node)
        if not children:
            return (node.text or "").strip()

        result: dict[str, Any] = {}
        for child in children:
            key = child.tag.split("}")[-1]
            value = convert(child)
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        return result

    return {element.tag.split("}")[-1]: convert(element)}


def _message(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    errors = payload.get("errors")
    if isinstance(errors, list) and errors and isinstance(errors[0], dict):
        return errors[0].get("description") or errors[0].get("message")
    status = payload.get("status")
    if isinstance(status, dict):
        return status.get("description")
    return payload.get("message") or payload.get("description")
