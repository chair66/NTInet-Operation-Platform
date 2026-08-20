from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

import httpx

from app.config import Settings, get_settings


logger = logging.getLogger("nop.plume")


class PlumeError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PlumeClient:
    """Plume Cloud client with cached M2M token management."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_lock = Lock()

    @property
    def configured(self) -> bool:
        return bool(
            self.settings.plume_authorization_token_url.strip()
            and self.settings.plume_authorization_header.strip()
            and self.settings.plume_scope.strip()
        )

    def _authorization_header(self) -> str:
        header = self.settings.plume_authorization_header.strip()
        if header.lower().startswith("basic:"):
            header = f"Basic {header.split(':', 1)[1].strip()}"
        if not header.lower().startswith("basic "):
            raise PlumeError("PLUME_AUTHORIZATION_HEADER must begin with 'Basic '.")
        return header

    def _token_is_valid(self) -> bool:
        if not self._access_token or not self._token_expires_at:
            return False
        grace = max(self.settings.plume_token_refresh_grace_seconds, 0)
        return datetime.now(timezone.utc) + timedelta(seconds=grace) < self._token_expires_at

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        if not self.configured:
            raise PlumeError("Plume M2M credentials are not configured.")
        if not force_refresh and self._token_is_valid():
            return self._access_token or ""

        with self._token_lock:
            if not force_refresh and self._token_is_valid():
                return self._access_token or ""
            try:
                response = httpx.post(
                    self.settings.plume_authorization_token_url.strip(),
                    headers={
                        "Authorization": self._authorization_header(),
                        "Accept": "application/json",
                        "Cache-Control": "no-cache",
                        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                    },
                    data={
                        "grant_type": "client_credentials",
                        "scope": self.settings.plume_scope.strip(),
                    },
                    timeout=self.settings.request_timeout_seconds,
                )
            except httpx.RequestError as exc:
                raise PlumeError(f"Unable to reach Plume authorization service: {exc}") from exc

            payload = self._json_payload(response)
            if response.is_error:
                error = payload.get("error_description") or payload.get("error")
                raise PlumeError(
                    f"Plume token request failed ({response.status_code}): {error or 'Unknown error'}",
                    status_code=response.status_code,
                )

            token = str(payload.get("access_token") or "").strip()
            if not token:
                raise PlumeError("Plume token response did not include access_token.")
            try:
                expires_in = max(int(payload.get("expires_in", 600)), 1)
            except (TypeError, ValueError):
                expires_in = 600
            self._access_token = token
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            logger.info("Obtained Plume bearer token with %s-second TTL", expires_in)
            return token

    def connection_status(self) -> dict[str, Any]:
        token = self.get_access_token(force_refresh=True)
        remaining = 0
        if self._token_expires_at:
            remaining = max(
                int((self._token_expires_at - datetime.now(timezone.utc)).total_seconds()),
                0,
            )
        return {
            "configured": True,
            "authenticated": bool(token),
            "expires_in": remaining,
            "scope": self.settings.plume_scope.strip(),
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        form_data: dict[str, Any] | None = None,
    ) -> Any:
        base_url = self.settings.plume_api_base_url.strip()
        if not base_url and not path.startswith(("https://", "http://")):
            raise PlumeError("PLUME_API_BASE_URL is not configured.")
        url = path if path.startswith(("https://", "http://")) else (
            f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        )
        try:
            response = httpx.request(
                method,
                url,
                params=params,
                json=json_body,
                data=form_data,
                headers={
                    "Authorization": f"Bearer {self.get_access_token()}",
                    "Accept": "application/json",
                },
                timeout=self.settings.request_timeout_seconds,
            )
        except httpx.RequestError as exc:
            raise PlumeError(f"Unable to reach Plume API: {exc}") from exc
        payload = self._json_payload(response)
        if response.is_error:
            message = payload.get("error_description") or payload.get("message") or payload.get("error")
            raise PlumeError(
                f"Plume API request failed ({response.status_code}): {message or 'Unknown error'}",
                status_code=response.status_code,
            )
        return payload

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Issue an authenticated read-only Plume API request."""
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        json_body: Any = None,
        form_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Issue an authenticated Plume action request."""
        return self.request(
            "POST", path, params=params, json_body=json_body, form_data=form_data
        )

    def put(self, path: str, *, json_body: Any = None) -> Any:
        """Issue an authenticated Plume action request."""
        return self.request("PUT", path, json_body=json_body)

    def delete(
        self,
        path: str,
        *,
        form_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Issue an authenticated Plume removal/unclaim request."""
        return self.request("DELETE", path, params=params, form_data=form_data)

    @staticmethod
    def _json_payload(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            return {"message": response.text[:500]}
        return payload if isinstance(payload, dict) else {"data": payload}


plume_client = PlumeClient()
