from __future__ import annotations

from app.database.models import User
from app.modules.registry import PlatformModule, module_registry


def available_modules_for_user(user: User) -> tuple[PlatformModule, ...]:
    available: list[PlatformModule] = []

    for module in module_registry.enabled():
        if module.staff_only and not user.organization.is_staff:
            continue
        if not user.has_module(module.slug):
            continue
        if module.permission and not user.can(module.permission):
            continue
        available.append(module)

    return tuple(available)


def user_can_access_module(user: User, module_slug: str) -> bool:
    module = module_registry.get(module_slug)

    if module is None or not module.enabled:
        return False

    if module.staff_only and not user.organization.is_staff:
        return False

    if not user.has_module(module.slug):
        return False

    return module.permission is None or user.can(module.permission)
