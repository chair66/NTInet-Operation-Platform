from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from fastapi import HTTPException, Request, status
from sqlalchemy import Select

from app.database.models import AuditLog, Role, User
from app.security.context import SecurityContext

T = TypeVar("T")


def context_from_request(request: Request) -> SecurityContext:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not user.active or not user.organization.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user or organization")
    return SecurityContext.from_user(user)


def is_platform_staff(context: SecurityContext) -> bool:
    return context.is_staff


def require_platform_staff(request: Request) -> SecurityContext:
    context = context_from_request(request)
    if not is_platform_staff(context):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This resource is restricted to NTInet platform staff")
    return context


def scope_users(statement: Select, context: SecurityContext) -> Select:
    return statement if is_platform_staff(context) else statement.where(User.organization_id == context.organization_id)


def scope_roles(statement: Select, context: SecurityContext) -> Select:
    if is_platform_staff(context):
        return statement
    return statement.where((Role.organization_id == context.organization_id) | (Role.organization_id.is_(None)))


def scope_audit_logs(statement: Select, context: SecurityContext) -> Select:
    return statement if is_platform_staff(context) else statement.where(AuditLog.organization_id == context.organization_id)


def require_same_organization(context: SecurityContext, organization_id: int) -> None:
    if not is_platform_staff(context) and int(organization_id) != context.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-organization access denied")


def validate_role_assignment(context: SecurityContext, target_organization_id: int, roles: Iterable[Role]) -> list[Role]:
    require_same_organization(context, target_organization_id)
    validated: list[Role] = []
    for role in roles:
        if role.organization_id not in (None, target_organization_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A role from another organization cannot be assigned")
        if not is_platform_staff(context) and role.name in {"Operations Admin", "Support", "Sales", "Read Only"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff roles cannot be assigned by reseller organizations")
        validated.append(role)
    return validated


def allowed_bandwidth_site_ids(context: SecurityContext) -> frozenset[int] | None:
    if context.is_staff:
        return None
    return context.organization.allowed_bandwidth_site_ids


def require_bandwidth_site(request: Request, site_id: int | str) -> int:
    context = context_from_request(request)
    try:
        normalized = int(site_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bandwidth site not found") from exc
    allowed = allowed_bandwidth_site_ids(context)
    if allowed is not None and normalized not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This Bandwidth sub-account is not assigned to your organization")
    return normalized


def visible_bandwidth_sites(request: Request, sites: Iterable[dict]) -> list[dict]:
    context = context_from_request(request)
    allowed = allowed_bandwidth_site_ids(context)
    if allowed is None:
        return list(sites)
    return [site for site in sites if _site_id(site) in allowed]


def filter_bandwidth_records(request: Request, records: Iterable[dict], *site_keys: str) -> list[dict]:
    context = context_from_request(request)
    allowed = allowed_bandwidth_site_ids(context)
    if allowed is None:
        return list(records)
    result = []
    for record in records:
        value = next((record.get(key) for key in site_keys if record.get(key) not in (None, "")), None)
        try:
            if int(value) in allowed:
                result.append(record)
        except (TypeError, ValueError):
            continue
    return result


def _site_id(site: dict) -> int | None:
    value = site.get("id", site.get("siteId", site.get("subAccountId")))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
