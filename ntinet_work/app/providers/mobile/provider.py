from app.providers.base import BaseProvider, ProviderDescriptor
from app.providers.mobile.client import BrandVNOClient
from app.providers.mobile.inventory import SIMInventoryService


class BrandVNOMobileProvider(BaseProvider):
    descriptor = ProviderDescriptor(
        slug="brandvno",
        name="BrandVNO / OXIO",
        provider_type="mobile-carrier",
        version="1.0",
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

    def __init__(self) -> None:
        self.client = BrandVNOClient()
        self.sim_inventory = SIMInventoryService(self.client)

    def validate_configuration(self) -> tuple[bool, str]:
        return self.client.validate_configuration()
