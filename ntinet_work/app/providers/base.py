from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    slug: str
    name: str
    provider_type: str
    version: str = "1.0"
    capabilities: frozenset[str] = field(default_factory=frozenset)


class BaseProvider(ABC):
    """Provider contract for external systems integrated with DigiCloud."""

    descriptor: ProviderDescriptor

    @abstractmethod
    def validate_configuration(self) -> tuple[bool, str]:
        """Return whether the provider is configured and a human-readable detail."""

    def supports(self, capability: str) -> bool:
        return capability in self.descriptor.capabilities

    def health(self) -> dict[str, Any]:
        valid, detail = self.validate_configuration()
        return {
            "slug": self.descriptor.slug,
            "name": self.descriptor.name,
            "type": self.descriptor.provider_type,
            "version": self.descriptor.version,
            "configured": valid,
            "detail": detail,
            "capabilities": sorted(self.descriptor.capabilities),
        }
