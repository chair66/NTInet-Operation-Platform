from __future__ import annotations

from dataclasses import dataclass
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    DigiCloudOrganizationSettings,
    DigiCloudUserHiddenDomain,
    Organization,
    User,
)
from app.modules.access import user_can_access_module
from app.providers.netsapiens import NetSapiensDomains, NetSapiensError


MODULE_SLUG = "digicloud-user-management"
PERMISSION = "digicloud.users.manage"
SPECIALIST_ROLE = "DigiCloud & Porting Specialist"


@dataclass(frozen=True)
class LiveResellerDomain:
    """A live DigiCloud domain scoped through an NOP organization's reseller link."""

    domain_name: str
    organization_id: int
    reseller: str
    organization: Organization
    description: str = ""
    active: bool = True
    user_management_enabled: bool = True
    id: int | None = None
    raw: dict | None = None


def require_user_management_access(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not user.can(PERMISSION):
        raise HTTPException(status_code=403, detail="DigiCloud User Management permission is required.")
    if not user_can_access_module(user, MODULE_SLUG):
        raise HTTPException(status_code=403, detail="DigiCloud User Management is not enabled for your organization.")
    return user


def is_specialist(user: User) -> bool:
    return any(role.name == SPECIALIST_ROLE for role in user.roles)


def _domain_name(row: dict) -> str:
    return str(row.get("domain") or row.get("domain_name") or row.get("name") or "").strip().lower().rstrip(".")


def _linked_organizations(db: Session, user: User) -> list[tuple[Organization, DigiCloudOrganizationSettings]]:
    stmt = (
        select(Organization, DigiCloudOrganizationSettings)
        .join(DigiCloudOrganizationSettings, DigiCloudOrganizationSettings.organization_id == Organization.id)
        .where(
            Organization.active.is_(True),
            Organization.deleted_at.is_(None),
            DigiCloudOrganizationSettings.active.is_(True),
            DigiCloudOrganizationSettings.netsapiens_reseller != "",
        )
        .order_by(Organization.name)
    )
    # Platform superusers may deliberately switch organizations. Everyone else,
    # including NTInet-staff specialists, is bounded by their own organization.
    if not user.is_superuser:
        stmt = stmt.where(Organization.id == user.organization_id)
    return list(db.execute(stmt).all())


def hidden_domain_names(db: Session, user_id: int) -> set[str]:
    return {
        str(value).strip().lower().rstrip(".")
        for value in db.scalars(
            select(DigiCloudUserHiddenDomain.domain_name).where(
                DigiCloudUserHiddenDomain.user_id == user_id
            )
        ).all()
        if str(value or "").strip()
    }


def base_user_domains(db: Session, user: User) -> list[LiveResellerDomain]:
    """Live domains granted by the user's organization/reseller before deny-list filtering."""
    provider = NetSapiensDomains()
    linked = _linked_organizations(db, user)
    if not linked:
        return []

    result: list[LiveResellerDomain] = []
    seen: set[tuple[int, str]] = set()
    errors: list[str] = []
    for organization, settings in linked:
        reseller = str(settings.netsapiens_reseller or "").strip()
        if not reseller:
            continue
        try:
            rows = provider.list(reseller)
        except NetSapiensError as exc:
            errors.append(f"{organization.effective_name}: {exc}")
            continue
        for row in rows:
            name = _domain_name(row)
            if not name:
                continue
            key = (organization.id, name)
            if key in seen:
                continue
            seen.add(key)
            result.append(
                LiveResellerDomain(
                    domain_name=name,
                    organization_id=organization.id,
                    reseller=reseller,
                    organization=organization,
                    description=str(row.get("description") or row.get("domain-description") or "").strip(),
                    raw=row,
                )
            )

    if not result and errors:
        raise HTTPException(status_code=502, detail="Unable to load DigiCloud reseller domains: " + "; ".join(errors))
    return sorted(result, key=lambda item: (item.organization.effective_name.casefold(), item.domain_name.casefold()))


def allowed_user_domains(db: Session, user: User) -> list[LiveResellerDomain]:
    """Organization/reseller scope minus domains explicitly hidden from this NOP user."""
    domains = base_user_domains(db, user)
    if user.is_superuser:
        return domains
    hidden = hidden_domain_names(db, user.id)
    if not hidden:
        return domains
    return [item for item in domains if item.domain_name not in hidden]


def require_allowed_domain(db: Session, user: User, domain_name: str) -> LiveResellerDomain:
    normalized = (domain_name or "").strip().lower().rstrip(".")
    for managed in allowed_user_domains(db, user):
        if managed.domain_name == normalized:
            return managed
    if normalized in hidden_domain_names(db, user.id):
        raise HTTPException(status_code=403, detail="This DigiCloud domain has been hidden from your account.")
    raise HTTPException(status_code=403, detail="This DigiCloud domain is not owned by your linked reseller.")


def admin_organizations(db: Session) -> list[Organization]:
    return list(
        db.scalars(
            select(Organization)
            .where(Organization.active.is_(True), Organization.deleted_at.is_(None))
            .order_by(Organization.name)
        ).all()
    )
