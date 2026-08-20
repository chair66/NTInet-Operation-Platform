from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status

from app.database.models import Organization, User
from app.security.authorization import (
    context_can_access_module,
    context_has_all_permissions,
    context_has_any_permission,
    context_has_organization_type,
    context_has_permission,
)
from app.security.context import SecurityContext


def get_authenticated_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_active_user(user: User = Depends(get_authenticated_user)) -> User:
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This user account is inactive")
    return user


def require_active_organization(user: User = Depends(require_active_user)) -> User:
    organization = getattr(user, "organization", None)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not associated with an organization",
        )
    if not organization.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This organization is inactive")
    return user


def get_security_context(user: User = Depends(require_active_organization)) -> SecurityContext:
    return SecurityContext.from_user(user)


def require_organization_type(*allowed_types: str) -> Callable[[SecurityContext], SecurityContext]:
    if not allowed_types:
        raise ValueError("At least one organization type must be provided")
    normalized_types = frozenset(value.strip().lower() for value in allowed_types)
    invalid_types = normalized_types - Organization.ALLOWED_TYPES
    if invalid_types:
        invalid = ", ".join(sorted(invalid_types))
        raise ValueError(f"Invalid organization types: {invalid}")

    def dependency(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
        if not context_has_organization_type(context, normalized_types):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organization type cannot access this resource",
            )
        return context

    return dependency


def require_staff(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
    if not context.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is restricted to NTInet staff",
        )
    return context


def require_reseller(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
    if not context.is_reseller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is restricted to reseller organizations",
        )
    return context


def require_module(module_slug: str) -> Callable[[SecurityContext], SecurityContext]:
    normalized_slug = module_slug.strip().lower()
    if not normalized_slug:
        raise ValueError("Module slug cannot be empty")

    def dependency(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
        if not context_can_access_module(context, normalized_slug):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organization does not have access to this module",
            )
        return context

    return dependency


def require_permission(permission: str) -> Callable[[SecurityContext], SecurityContext]:
    normalized_permission = permission.strip()
    if not normalized_permission:
        raise ValueError("Permission cannot be empty")

    def dependency(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
        if not context_has_permission(context, normalized_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return context

    return dependency


def require_any_permission(*permissions: str) -> Callable[[SecurityContext], SecurityContext]:
    normalized_permissions = tuple(value.strip() for value in permissions if value.strip())
    if not normalized_permissions:
        raise ValueError("At least one permission must be provided")

    def dependency(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
        if not context_has_any_permission(context, normalized_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have any of the required permissions",
            )
        return context

    return dependency


def require_all_permissions(*permissions: str) -> Callable[[SecurityContext], SecurityContext]:
    normalized_permissions = tuple(value.strip() for value in permissions if value.strip())
    if not normalized_permissions:
        raise ValueError("At least one permission must be provided")

    def dependency(context: SecurityContext = Depends(get_security_context)) -> SecurityContext:
        if not context_has_all_permissions(context, normalized_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have all required permissions",
            )
        return context

    return dependency
