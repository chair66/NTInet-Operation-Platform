from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.providers.base import ProviderClient
from app.providers.mobile.exceptions import MobileProviderConfigurationError


class BrandVNOClient(ProviderClient):
    """BrandVNO/OXIO API client using NOP's shared provider transport."""

    provider_slug = "BrandVNO"

    def __init__(self) -> None:
        self.settings = get_settings()
        headers = {
            "Accept": "application/json",
            "User-Agent": f"NOP/{self.settings.app_version}",
        }
        auth: httpx.Auth | None = None
        token = self.settings.oxio_basic_auth.strip()
        if token:
            if token.lower().startswith("basic "):
                token = token[6:].strip()
            headers["Authorization"] = f"Basic {token}"
        elif self.settings.oxio_api_key and self.settings.oxio_api_secret:
            auth = httpx.BasicAuth(
                self.settings.oxio_api_key,
                self.settings.oxio_api_secret,
            )

        super().__init__(
            base_url=self.selected_base_url,
            timeout_seconds=self.settings.request_timeout_seconds,
            max_attempts=self.settings.provider_retry_attempts,
            backoff_seconds=self.settings.provider_retry_backoff_seconds,
            headers=headers,
            auth=auth,
        )

    @property
    def selected_base_url(self) -> str:
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
        if not self.selected_base_url:
            missing.append("OXIO base URL")
        if not self.settings.oxio_sim_inventory_path.strip():
            missing.append("OXIO_SIM_INVENTORY_PATH")
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
        return await self.request_json("GET", path, params=params)
