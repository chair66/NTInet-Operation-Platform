class MobileProviderError(RuntimeError):
    """Base exception for mobile provider operations."""


class MobileProviderConfigurationError(MobileProviderError):
    """Raised when required provider configuration is missing."""


class MobileProviderRequestError(MobileProviderError):
    """Raised when the provider API rejects or cannot complete a request."""
