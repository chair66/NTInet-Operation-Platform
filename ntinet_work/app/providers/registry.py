from __future__ import annotations

from threading import RLock
from app.providers.base import BaseProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._lock = RLock()

    def register(self, provider: BaseProvider, *, replace: bool = False) -> None:
        slug = provider.descriptor.slug
        with self._lock:
            if slug in self._providers and not replace:
                raise ValueError(f"Provider '{slug}' is already registered")
            self._providers[slug] = provider

    def get(self, slug: str) -> BaseProvider:
        try:
            return self._providers[slug]
        except KeyError as exc:
            raise LookupError(f"Provider '{slug}' is not registered") from exc

    def all(self) -> tuple[BaseProvider, ...]:
        return tuple(self._providers[key] for key in sorted(self._providers))


provider_registry = ProviderRegistry()
