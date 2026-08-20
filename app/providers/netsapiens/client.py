from __future__ import annotations
import httpx
import logging
from collections import deque
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from app.config import get_settings

logger = logging.getLogger("digicloud.netsapiens")
NETSAPIENS_API_LOG: deque[dict[str, Any]] = deque(maxlen=250)


class NetSapiensError(RuntimeError):
    pass


def _looks_like_html(response: httpx.Response, body: Any) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" in content_type or "application/xhtml" in content_type:
        return True
    if not isinstance(body, str):
        return False
    prefix = body.lstrip().lower()[:200]
    return prefix.startswith("<!doctype html") or prefix.startswith("<html")

class NetSapiensClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.netsapiens_api_url and self.settings.netsapiens_token)


    def inspect(self, method: str, path: str, *, params=None, json=None) -> dict[str, Any]:
        """Return safe request/response diagnostics without exposing credentials."""
        if not self.configured:
            raise NetSapiensError("NetSapiens API is not configured")
        url = f"{self.settings.netsapiens_api_url.rstrip('/')}/{path.lstrip('/')}"
        safe_request_headers = {"Accept": "application/json", "Authorization": "Bearer ***REDACTED***"}
        headers = {"Authorization": f"Bearer {self.settings.netsapiens_token}", "Accept": "application/json"}
        try:
            response = httpx.request(
                method, url, headers=headers, params=params, json=json,
                timeout=self.settings.request_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            return {
                "request": {"method": method.upper(), "url": url, "params": params or {}, "headers": safe_request_headers},
                "response": {"status_code": None, "headers": {}, "body": None},
                "error": str(exc),
            }
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = response.text
        safe_response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() in {"content-type", "content-length", "date", "server", "x-request-id"}
        }
        return {
            "request": {
                "method": method.upper(),
                "url": str(response.request.url),
                "params": params or {},
                "headers": safe_request_headers,
            },
            "response": {
                "status_code": response.status_code,
                "headers": safe_response_headers,
                "body": body,
            },
            "error": None,
        }

    def request(self, method: str, path: str, *, params=None, json=None):
        if not self.configured:
            raise NetSapiensError("NetSapiens API is not configured")
        url = f"{self.settings.netsapiens_api_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.settings.netsapiens_token}", "Accept": "application/json"}
        started = perf_counter()
        try:
            response = httpx.request(
                method, url, headers=headers, params=params, json=json,
                timeout=self.settings.request_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            latency = round((perf_counter() - started) * 1000)
            self._record(method, url, None, latency, params, json, None, str(exc))
            raise NetSapiensError(str(exc)) from exc

        latency = round((perf_counter() - started) * 1000)
        try:
            response_body = response.json() if response.content else {}
        except ValueError:
            response_body = response.text
        self._record(
            method, str(response.request.url), response.status_code, latency,
            params, json, response_body, None,
        )

        if response.status_code >= 400:
            raise NetSapiensError(f"NetSapiens HTTP {response.status_code}: {response.text[:500]}")
        if not response.content:
            return {}
        if _looks_like_html(response, response_body):
            raise NetSapiensError(
                "NetSapiens returned an HTML page instead of an API response; "
                "authentication may have expired or the endpoint may be incorrect"
            )
        return response_body if not isinstance(response_body, str) else {"raw": response_body}

    def _record(self, method, url, status, latency, params, request_json, response_body, error):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "NetSapiens",
            "method": str(method).upper(),
            "url": url,
            "status": status,
            "latency_ms": latency,
            "params": params or {},
            "payload": {
                "request": {"params": params or {}, "json": request_json},
                "response": {"status": status, "body": response_body},
                "error": error,
            },
        }
        NETSAPIENS_API_LOG.appendleft(event)
        logger.info("%s %s -> %s (%sms)", str(method).upper(), url, status, latency)
