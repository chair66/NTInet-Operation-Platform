from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

import httpx

from app.config import get_settings
from app.database.communication_models import CommunicationProfile
from app.services.communication_profile_service import CommunicationProfileService


settings = get_settings()
BANDWIDTH_MESSAGING_API_LOG: deque[dict[str, Any]] = deque(maxlen=settings.api_log_limit)
_TOKEN_CACHE: dict[tuple[str, str], tuple[str, datetime]] = {}


class BandwidthMessagingClient:
    """Synchronous Bandwidth Messaging client for ticket and customer workflows."""

    def _oauth_credentials(self, profile: CommunicationProfile) -> tuple[str, str, str]:
        if profile.bandwidth_auth_mode == "oauth2_system":
            return settings.bandwidth_client_id, settings.bandwidth_client_secret, settings.bandwidth_token_url
        return (
            profile.bandwidth_client_id,
            CommunicationProfileService.client_secret(profile),
            profile.bandwidth_token_url or settings.bandwidth_token_url,
        )

    def _access_token(self, profile: CommunicationProfile) -> str:
        client_id, client_secret, token_url = self._oauth_credentials(profile)
        if not client_id or not client_secret:
            raise RuntimeError("Bandwidth OAuth client ID and client secret are required.")
        cache_key = (token_url, client_id)
        cached = _TOKEN_CACHE.get(cache_key)
        now = datetime.now(timezone.utc)
        if cached and now < cached[1]:
            return cached[0]

        started = perf_counter()
        try:
            response = httpx.post(
                token_url,
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
                headers={"Accept": "application/json"},
                timeout=settings.request_timeout_seconds,
                follow_redirects=True,
            )
            payload = _safe_payload(response)
            self._record("POST", token_url, response.status_code, started, _redact(payload), {"grant_type": "client_credentials"})
            response.raise_for_status()
        except httpx.RequestError as exc:
            self._record("POST", token_url, None, started, str(exc))
            raise RuntimeError(f"Unable to reach the Bandwidth OAuth service: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Bandwidth OAuth authentication failed: {_error_message(payload)}") from exc

        if not isinstance(payload, dict) or not payload.get("access_token"):
            raise RuntimeError("Bandwidth OAuth response did not include an access token.")
        expires_in = max(int(payload.get("expires_in", 3600)) - 60, 60)
        token = str(payload["access_token"])
        _TOKEN_CACHE[cache_key] = (token, now + timedelta(seconds=expires_in))
        return token

    def test_auth(self, profile: CommunicationProfile) -> str:
        if not profile.credential_configured:
            raise RuntimeError("Required Bandwidth profile configuration is incomplete.")
        if profile.bandwidth_auth_mode == "basic":
            return "Legacy Basic credentials are configured. No SMS was sent."
        self._access_token(profile)
        return "Bandwidth OAuth authentication succeeded. No SMS was sent."

    def send_sms(self, profile: CommunicationProfile, destination: str, text: str, tag: str) -> str:
        if not profile.credential_configured:
            raise RuntimeError("Bandwidth Messaging profile configuration is incomplete.")
        base = profile.bandwidth_api_base.rstrip("/")
        if "/users/" in base:
            base = base.split("/users/", 1)[0].rstrip("/")
        url = f"{base}/users/{profile.bandwidth_account_id}/messages"
        body = {
            "to": [destination],
            "from": profile.sender_address,
            "text": text[:1500],
            "applicationId": profile.bandwidth_application_id,
            "tag": tag,
        }
        kwargs: dict[str, Any] = {}
        if profile.bandwidth_auth_mode == "basic":
            kwargs["auth"] = (profile.bandwidth_username, CommunicationProfileService.password(profile))
        else:
            kwargs["headers"] = {"Authorization": f"Bearer {self._access_token(profile)}", "Accept": "application/json"}

        started = perf_counter()
        try:
            response = httpx.post(url, json=body, timeout=settings.request_timeout_seconds, follow_redirects=True, **kwargs)
            payload = _safe_payload(response)
            safe_body = {**body, "text": f"[redacted {len(body['text'])} characters]"}
            self._record("POST", url, response.status_code, started, payload, safe_body)
            response.raise_for_status()
        except httpx.RequestError as exc:
            self._record("POST", url, None, started, str(exc))
            raise RuntimeError(f"Unable to reach Bandwidth Messaging: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Bandwidth Messaging request failed: {_error_message(payload)}") from exc
        if not isinstance(payload, dict):
            return ""
        return str(payload.get("id") or payload.get("messageId") or "")

    @staticmethod
    def _record(method: str, url: str, status: int | None, started: float, payload: Any, params: Any = None) -> None:
        BANDWIDTH_MESSAGING_API_LOG.appendleft({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "Bandwidth Messaging",
            "method": method,
            "url": url,
            "status": status,
            "latency_ms": round((perf_counter() - started) * 1000),
            "params": params or {},
            "payload": payload,
        })


def _safe_payload(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text[:2000]


def _redact(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    return {key: ("[redacted]" if key.lower() in {"access_token", "refresh_token", "id_token"} else value) for key, value in payload.items()}


def _error_message(payload: Any) -> str:
    if isinstance(payload, dict):
        return str(payload.get("error_description") or payload.get("description") or payload.get("message") or payload.get("error") or payload)
    return str(payload)
