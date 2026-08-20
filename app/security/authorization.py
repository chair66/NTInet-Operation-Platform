from __future__ import annotations

from collections.abc import Collection

from app.modules.registry import module_registry
from app.security.context import SecurityContext


def context_can_access_module(context: SecurityContext, module_slug: str) -> bool:
    module = module_registry.get(module_slug)
    if module is None or not module.enabled:
        return False
    if not context.has_module_assignment(module_slug):
        return False
    if module.permission and not context.can(module.permission):
        return False
    return True


def context_has_permission(context: SecurityContext, permission: str) -> bool:
    return context.can(permission)


def context_has_any_permission(context: SecurityContext, permissions: Collection[str]) -> bool:
    return any(context.can(permission) for permission in permissions)


def context_has_all_permissions(context: SecurityContext, permissions: Collection[str]) -> bool:
    return all(context.can(permission) for permission in permissions)


def context_has_organization_type(context: SecurityContext, allowed_types: Collection[str]) -> bool:
    normalized = {value.strip().lower() for value in allowed_types}
    return context.organization.organization_type in normalized
