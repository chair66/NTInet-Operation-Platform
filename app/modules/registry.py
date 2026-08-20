from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformModule:
    slug: str
    name: str
    icon: str
    enabled: bool = True
    provider_slug: str | None = None
    permission: str | None = None
    staff_only: bool = False


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, PlatformModule] = {}

    def register(self, module: PlatformModule, *, replace: bool = False) -> None:
        if module.slug in self._modules and not replace:
            raise ValueError(f"Module '{module.slug}' is already registered")
        self._modules[module.slug] = module

    def get(self, slug: str) -> PlatformModule | None:
        return self._modules.get(slug)

    def all(self) -> tuple[PlatformModule, ...]:
        return tuple(self._modules.values())

    def enabled(self) -> tuple[PlatformModule, ...]:
        return tuple(module for module in self._modules.values() if module.enabled)


module_registry = ModuleRegistry()


def register_builtin_modules() -> None:
    modules = (
        PlatformModule(
            "dashboard",
            "Dashboard",
            "fa-house",
            permission="dashboard.read",
        ),
        PlatformModule(
            "lnp-management",
            "LNP Management",
            "fa-phone",
            provider_slug="bandwidth",
            permission="numbers.read",
        ),
        PlatformModule(
            "digicloud",
            "DigiCloud",
            "fa-cloud",
            provider_slug="netsapiens",
            permission="digicloud.view",
        ),
        PlatformModule(
            "digicloud-user-management",
            "DigiCloud User Management",
            "fa-users",
            provider_slug="netsapiens",
            permission="digicloud.users.manage",
        ),
        PlatformModule(
            "nti-mobile",
            "NTI Mobile",
            "fa-mobile-screen",
            enabled=True,
            provider_slug="mobile",
            permission="nti_mobile.view",
            staff_only=True,
        ),
        PlatformModule(
            "reporting",
            "Reporting",
            "fa-chart-line",
            enabled=False,
            permission="reports.view",
        ),
        PlatformModule(
            "administration",
            "Administration",
            "fa-shield-halved",
            permission="admin.users",
            staff_only=True,
        ),
    )

    for module in modules:
        module_registry.register(module, replace=True)
