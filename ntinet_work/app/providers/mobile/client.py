from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.providers.mobile.exceptions import (
    MobileProviderConfigurationError,
    MobileProviderRequestError,
)


class BrandVNOClient:
    """Small async HTTP client for the OXIO/BrandVNO API."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def base_url(self) -> str:
        environment = self.settings.oxio_env.strip().lower()
        if environment == "production":
            return self.settings.oxio_production_base_url.rstrip("/")
        return self.settings.oxio_staging_base_url.rstrip("/")

    def validate_configuration(self) -> tuple[bool, str]:
        missing: list[str] = []
        has_basic_token = bool(self.settings.oxio_basic_auth.strip())
        if not has_basic_token and not self.settings.oxio_api_key:
            missing.append("OXIO_API_KEY")
        if not has_basic_token and not self.settings.oxio_api_secret:
            missing.append("OXIO_API_SECRET")
        if not self.base_url:
            missing.append("OXIO base URL")
        if missing:
            return False, f"Missing {', '.join(missing)}"
        return True, f"Configured for {self.settings.oxio_env}"

    async def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        valid, detail = self.validate_configuration()
        if not valid:
            raise MobileProviderConfigurationError(detail)
        if not path.strip():
            raise MobileProviderConfigurationError(
                "OXIO_SIM_INVENTORY_PATH is not configured. Add the SIM inventory "
                "endpoint path from the BrandVNO documentation to .env."
            )

        normalized_path = path if path.startswith("/") else f"/{path}"
        try:
            headers = {
                "Accept": "application/json",
                "User-Agent": f"NTInet-Operations/{self.settings.app_version}",
            }
            auth = None
            basic_token = self.settings.oxio_basic_auth.strip()
            if basic_token:
                if basic_token.lower().startswith("basic "):
                    basic_token = basic_token[6:].strip()
                headers["Authorization"] = f"Basic {basic_token}"
            else:
                auth = httpx.BasicAuth(
                    self.settings.oxio_api_key,
                    self.settings.oxio_api_secret,
                )

            async with httpx.AsyncClient(
                base_url=self.base_url,
                auth=auth,
                timeout=self.settings.request_timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get(normalized_path, params=params)
        except httpx.TimeoutException as exc:
            raise MobileProviderRequestError(
                "BrandVNO did not respond before the request timed out."
            ) from exc
        except httpx.HTTPError as exc:
            raise MobileProviderRequestError(
                f"Unable to connect to BrandVNO: {exc}"
            ) from exc

        if response.is_error:
            request_id = response.headers.get("x-request-id", "")
            detail = ""
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = str(
                        payload.get("message")
                        or payload.get("detail")
                        or payload.get("error")
                        or ""
                    )
            except ValueError:
                detail = response.text[:300].strip()

            suffix = f" Request ID: {request_id}." if request_id else ""
            message = f"BrandVNO returned HTTP {response.status_code}."
            if detail:
                message += f" {detail}"
            raise MobileProviderRequestError(message + suffix)

        try:
            return response.json()
        except ValueError as exc:
            raise MobileProviderRequestError(
                "BrandVNO returned a response that was not valid JSON."
            ) from exc
