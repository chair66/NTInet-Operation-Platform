from app.providers.base import (
    ProviderConfigurationError,
    ProviderError,
    ProviderRequestError,
)


MobileProviderError = ProviderError
MobileProviderConfigurationError = ProviderConfigurationError
MobileProviderRequestError = ProviderRequestError


__all__ = [
    "MobileProviderError",
    "MobileProviderConfigurationError",
    "MobileProviderRequestError",
]
