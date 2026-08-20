from app.config import get_settings
from app.providers.base import BaseProvider, ProviderDescriptor


class BandwidthProvider(BaseProvider):
    """Platform adapter around the existing Bandwidth service layer.

    Sprint 1 keeps current routers and services unchanged. Sprint 2 can migrate
    operations into this provider one workflow at a time.
    """

    descriptor = ProviderDescriptor(
        slug="bandwidth",
        name="Bandwidth",
        provider_type="carrier",
        version="1.0",
        environment="production",
        capabilities=frozenset({
            "numbers.read", "numbers.buy", "numbers.move", "numbers.features",
            "ports.read", "ports.create", "ports.manage", "csr.read", "csr.create",
            "locations.create",
        }),
    )

    def validate_configuration(self) -> tuple[bool, str]:
        settings = get_settings()
        required = {
            "account ID": settings.bandwidth_account_id,
            "client ID": settings.bandwidth_client_id,
            "client secret": settings.bandwidth_client_secret,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            return False, f"Missing {', '.join(missing)}"
        return True, "Configured"
