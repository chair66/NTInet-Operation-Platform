from __future__ import annotations

import time

from app.config import get_settings
from app.providers.base import BaseProvider, ProviderDescriptor, ProviderHealth
from app.providers.mobile.client import BrandVNOClient
from app.providers.mobile.inventory import SIMInventoryService


class BrandVNOMobileProvider(BaseProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.descriptor = ProviderDescriptor(
            slug="brandvno",
            name="BrandVNO / OXIO",
            provider_type="mobile-carrier",
            version="1.0",
            environment=settings.oxio_env,
            capabilities=frozenset({
                "sims.read",
                "sims.refresh",
                "lines.activate",
                "lines.suspend",
                "lines.resume",
                "plans.read",
                "usage.read",
                "ports.create",
                "ports.read",
            }),
        )
        self.client = BrandVNOClient()
        self.sim_inventory = SIMInventoryService(self.client)

    def validate_configuration(self) -> tuple[bool, str]:
        return self.client.validate_configuration()

    async def check_health(self) -> ProviderHealth:
        valid, detail = self.validate_configuration()
        if not valid:
            return ProviderHealth(
                slug=self.descriptor.slug,
                name=self.descriptor.name,
                provider_type=self.descriptor.provider_type,
                environment=self.descriptor.environment,
                configured=False,
                status="not_configured",
                detail=detail,
            )

        started = time.perf_counter()
        try:
            # The configured inventory endpoint is a meaningful read-only health check.
            await self.client.get_json(
                get_settings().oxio_sim_inventory_path,
                params={
                    get_settings().oxio_sim_page_size_parameter: 1,
                },
            )
            elapsed = int((time.perf_counter() - started) * 1000)
            return ProviderHealth(
                slug=self.descriptor.slug,
                name=self.descriptor.name,
                provider_type=self.descriptor.provider_type,
                environment=self.descriptor.environment,
                configured=True,
                status="online",
                detail="API connection succeeded.",
                response_time_ms=elapsed,
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - started) * 1000)
            return ProviderHealth(
                slug=self.descriptor.slug,
                name=self.descriptor.name,
                provider_type=self.descriptor.provider_type,
                environment=self.descriptor.environment,
                configured=True,
                status="offline",
                detail=str(exc),
                response_time_ms=elapsed,
            )
