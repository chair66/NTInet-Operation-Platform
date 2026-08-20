from app.providers.bandwidth.provider import BandwidthProvider
from app.providers.mobile.provider import BrandVNOMobileProvider
from app.providers.registry import provider_registry


def register_builtin_providers() -> None:
    for provider in (BandwidthProvider(), BrandVNOMobileProvider()):
        try:
            provider_registry.register(provider)
        except ValueError:
            pass


__all__ = [
    "provider_registry",
    "register_builtin_providers",
    "BandwidthProvider",
    "BrandVNOMobileProvider",
]
