from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil
import re

from fastapi import HTTPException, Request
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.database.models import AuditLog, Organization, OrganizationModule, Role, User
from app.modules.registry import PlatformModule, module_registry
from app.security.context import SecurityContext
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


@dataclass(slots=True)
class OrganizationSummary:
    organization: Organization
    user_count: int
    active_user_count: int
    role_count: int
    module_count: int
    last_login_at: datetime | None
    last_activity_at: datetime | None
    health: str
    health_detail: str


@dataclass(slots=True)
class OrganizationPage:
    items: list[OrganizationSummary]
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        return max(1, ceil(self.total / self.per_page))

    @property
    def first_item(self) -> int:
        return 0 if self.total == 0 else ((self.page - 1) * self.per_page) + 1

    @property
    def last_item(self) -> int:
        return min(self.page * self.per_page, self.total)


@dataclass(slots=True)
class OrganizationService:
    db: Session
    context: SecurityContext
    request: Request | None = None

    ALLOWED_STATUSES = frozenset({"active", "suspended", "disabled", "deleted"})

    @property
    def audit(self) -> AuditService:
        return AuditService(self.db, self.request, self.context)

    def _require_staff(self) -> None:
        if not (self.context.is_staff and self.context.is_superuser):
            raise HTTPException(403, "Only NTInet staff can manage organizations")

    def list_page(self, *, query: str = "", status_filter: str = "all", sort: str = "name", direction: str = "asc", page: int = 1, per_page: int = 25) -> OrganizationPage:
        self._require_staff()
        page = max(1, int(page))
        per_page = max(10, min(int(per_page), 100))
        statement = select(Organization)
        if status_filter != "deleted":
            statement = statement.where(Organization.deleted_at.is_(None))
        if query.strip():
            term = f"%{query.strip().lower()}%"
            statement = statement.where(or_(func.lower(Organization.name).like(term), func.lower(Organization.slug).like(term), func.lower(func.coalesce(Organization.display_name, "")).like(term)))
        if status_filter in {"active", "suspended", "disabled"}:
            statement = statement.where(Organization.status == status_filter, Organization.deleted_at.is_(None))
        elif status_filter == "deleted":
            statement = statement.where(Organization.deleted_at.is_not(None))
        elif status_filter == "reseller":
            statement = statement.where(Organization.organization_type == Organization.RESELLER_TYPE)
        elif status_filter == "staff":
            statement = statement.where(Organization.organization_type == Organization.STAFF_TYPE)
        total = int(self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0)
        pages = max(1, ceil(total / per_page))
        page = min(page, pages)
        sort_columns = {
            "name": Organization.name,
            "type": Organization.organization_type,
            "status": Organization.status,
            "created": Organization.id,
        }
        column = sort_columns.get(sort, Organization.name)
        statement = statement.order_by(column.desc() if direction == "desc" else column.asc(), Organization.id.asc()).offset((page - 1) * per_page).limit(per_page)
        organizations = list(self.db.scalars(statement))
        return OrganizationPage([self.summary(org) for org in organizations], page, per_page, total)

    def dashboard_counts(self) -> dict[str, int]:
        self._require_staff()
        rows = self.db.execute(select(Organization.status, func.count(Organization.id)).where(Organization.deleted_at.is_(None)).group_by(Organization.status)).all()
        counts = {status: int(count) for status, count in rows}
        return {
            "organizations": sum(counts.values()),
            "active": counts.get("active", 0),
            "suspended": counts.get("suspended", 0),
            "disabled": counts.get("disabled", 0),
            "users": int(self.db.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None))) or 0),
        }

    def get(self, organization_id: int, *, include_deleted: bool = True) -> Organization:
        self._require_staff()
        statement = select(Organization).where(Organization.id == int(organization_id))
        if not include_deleted:
            statement = statement.where(Organization.deleted_at.is_(None))
        organization = self.db.scalar(statement)
        if not organization:
            raise HTTPException(404, "Organization not found")
        return organization

    def summary(self, organization: Organization) -> OrganizationSummary:
        user_count = int(self.db.scalar(select(func.count(User.id)).where(User.organization_id == organization.id, User.deleted_at.is_(None))) or 0)
        active_user_count = int(self.db.scalar(select(func.count(User.id)).where(User.organization_id == organization.id, User.deleted_at.is_(None), User.active.is_(True))) or 0)
        role_count = int(self.db.scalar(select(func.count(Role.id)).where(Role.organization_id == organization.id)) or 0)
        enabled_module_slugs = [module.slug for module in module_registry.enabled()]
        module_count = int(self.db.scalar(select(func.count(OrganizationModule.id)).where(OrganizationModule.organization_id == organization.id, OrganizationModule.enabled.is_(True), OrganizationModule.module_slug.in_(enabled_module_slugs))) or 0)
        last_login_at = self.db.scalar(select(func.max(User.last_login_at)).where(User.organization_id == organization.id))
        last_activity_at = self.db.scalar(select(func.max(AuditLog.created_at)).where(AuditLog.organization_id == organization.id))
        health, detail = self.health(organization, active_user_count, module_count)
        return OrganizationSummary(organization, user_count, active_user_count, role_count, module_count, last_login_at, last_activity_at, health, detail)

    @staticmethod
    def health(organization: Organization, active_users: int, enabled_modules: int) -> tuple[str, str]:
        if organization.deleted_at is not None or organization.status == "deleted":
            return "critical", "Organization is deleted"
        if organization.status in {"disabled", "suspended"} or not organization.active:
            return "critical", f"Organization is {organization.status}"
        warnings: list[str] = []
        if active_users == 0:
            warnings.append("No active users")
        if enabled_modules == 0:
            warnings.append("No enabled modules")
        if organization.is_reseller and not organization.allowed_bandwidth_site_ids:
            warnings.append("No Bandwidth sites assigned")
        return ("warning", "; ".join(warnings)) if warnings else ("healthy", "No issues detected")

    def create(self, *, name: str, display_name: str = "", organization_type: str = "reseller", status: str = "active", notes: str = "") -> Organization:
        self._require_staff()
        normalized_name = self._name(name)
        slug = self._unique_slug(normalized_name)
        organization_type = self._type(organization_type)
        status = self._status(status)
        self._name_free(normalized_name)
        organization = Organization(name=normalized_name, display_name=self._optional_name(display_name), slug=slug, organization_type=organization_type, status=status, active=status == "active", notes=notes.strip())
        self.db.add(organization)
        self.db.flush()
        default_modules = {"dashboard"}
        if organization.is_staff:
            default_modules.add("administration")
        self._replace_modules(organization, default_modules)
        self.audit.record("organization.create", "organization", organization.id, f"Created {organization.name}", module="identity", organization_id=organization.id, event_data={"name": organization.name, "type": organization.organization_type, "status": organization.status, "modules": sorted(default_modules)})
        NotificationService(self.db, self.context).publish("organization.created", subject=f"Organization created: {organization.name}", organization_id=organization.id, payload={"organization_id": organization.id, "status": organization.status})
        return organization

    def update(self, organization_id: int, *, name: str, display_name: str = "", organization_type: str = "reseller", status: str = "active", notes: str = "") -> Organization:
        self._require_staff()
        organization = self.get(organization_id)
        if organization.deleted_at is not None:
            raise HTTPException(400, "Restore the organization before editing it")
        old = {"name": organization.name, "display_name": organization.display_name, "type": organization.organization_type, "status": organization.status, "notes": organization.notes}
        organization.name = self._name(name)
        self._name_free(organization.name, organization.id)
        organization.display_name = self._optional_name(display_name)
        organization.organization_type = self._type(organization_type)
        organization.status = self._status(status)
        organization.active = organization.status == "active"
        organization.notes = notes.strip()
        self.audit.record("organization.update", "organization", organization.id, f"Updated {organization.name}", module="identity", organization_id=organization.id, event_data={"before": old, "after": {"name": organization.name, "display_name": organization.display_name, "type": organization.organization_type, "status": organization.status, "notes": organization.notes}})
        return organization

    def set_status(self, organization_id: int, status: str) -> Organization:
        self._require_staff()
        organization = self.get(organization_id)
        if organization.deleted_at is not None:
            raise HTTPException(400, "Restore the organization before changing its status")
        status = self._status(status)
        if status == "deleted":
            return self.soft_delete(organization_id)
        if status == "active" and not any(item.enabled for item in organization.modules):
            raise HTTPException(400, "Enable at least one module before activating the organization")
        organization.status = status
        organization.active = status == "active"
        self.audit.record("organization.status", "organization", organization.id, f"Status={status}", module="identity", organization_id=organization.id, event_data={"status": status})
        return organization

    def soft_delete(self, organization_id: int) -> Organization:
        self._require_staff()
        organization = self.get(organization_id)
        if organization.is_protected:
            raise HTTPException(400, "The protected NTInet system organization cannot be deleted")
        if organization.id == self.context.organization_id:
            raise HTTPException(400, "You cannot delete your own organization")
        if organization.deleted_at is None:
            organization.deleted_at = datetime.now(timezone.utc)
            organization.deleted_by_user_id = self.context.user_id
            organization.status = "deleted"
            organization.active = False
            self.db.execute(select(User).where(User.organization_id == organization.id))
            for user in organization.users:
                user.active = False
            self.audit.record("organization.delete", "organization", organization.id, "Soft deleted", module="identity", organization_id=organization.id)
        return organization

    def restore(self, organization_id: int) -> Organization:
        self._require_staff()
        organization = self.get(organization_id)
        organization.deleted_at = None
        organization.deleted_by_user_id = None
        organization.status = "disabled"
        organization.active = False
        self.audit.record("organization.restore", "organization", organization.id, "Restored as disabled", module="identity", organization_id=organization.id)
        return organization

    def available_modules(self, organization: Organization) -> tuple[PlatformModule, ...]:
        self._require_staff()
        return tuple(
            item for item in module_registry.enabled()
            if organization.is_staff or not item.staff_only
        )

    def module_assignments(self, organization: Organization) -> dict[str, bool]:
        return {item.module_slug: bool(item.enabled) for item in organization.modules}

    def update_modules(self, organization_id: int, module_slugs: list[str]) -> Organization:
        self._require_staff()
        organization = self.get(organization_id)
        if organization.is_deleted:
            raise HTTPException(400, "Restore the organization before changing modules")
        requested = {value.strip() for value in module_slugs if value.strip()}
        allowed = {item.slug for item in self.available_modules(organization)}
        invalid = requested - allowed
        if invalid:
            raise HTTPException(400, f"Invalid module assignment: {', '.join(sorted(invalid))}")
        if organization.status == "active" and not requested:
            raise HTTPException(400, "An active organization must have at least one enabled module")
        before = sorted(slug for slug, enabled in self.module_assignments(organization).items() if enabled)
        self._replace_modules(organization, requested)
        self.audit.record(
            "organization.modules.update", "organization", organization.id,
            "Updated module assignments", module="administration",
            organization_id=organization.id,
            event_data={"before": before, "after": sorted(requested)},
        )
        NotificationService(self.db, self.context).publish(
            "organization.modules.updated",
            subject=f"Modules updated: {organization.name}",
            organization_id=organization.id,
            payload={"organization_id": organization.id, "modules": sorted(requested)},
        )
        return organization

    def update_settings(
        self,
        organization_id: int,
        *,
        mfa_policy: str,
        password_expiration_days: int,
        session_timeout_minutes: int,
        allow_api_access: bool,
        timezone_name: str,
        date_format: str,
        default_role_id: int | None,
    ) -> Organization:
        self._require_staff()
        organization = self.get(organization_id)
        if organization.is_deleted:
            raise HTTPException(400, "Restore the organization before changing settings")
        mfa_policy = mfa_policy.strip().lower()
        if mfa_policy not in {"optional", "required"}:
            raise HTTPException(400, "MFA policy must be optional or required")
        password_expiration_days = int(password_expiration_days)
        if password_expiration_days not in {0, 30, 60, 90, 180, 365}:
            raise HTTPException(400, "Invalid password expiration period")
        session_timeout_minutes = int(session_timeout_minutes)
        if not 15 <= session_timeout_minutes <= 1440:
            raise HTTPException(400, "Session timeout must be between 15 and 1440 minutes")
        timezone_name = timezone_name.strip()
        if not timezone_name or len(timezone_name) > 64:
            raise HTTPException(400, "Invalid time zone")
        date_format = date_format.strip().upper()
        if date_format not in {"MM/DD/YYYY", "YYYY-MM-DD"}:
            raise HTTPException(400, "Invalid date format")
        if default_role_id:
            role = self.db.get(Role, int(default_role_id))
            if not role or (role.organization_id not in {None, organization.id}):
                raise HTTPException(400, "Default role is not available to this organization")
            default_role_id = role.id
        else:
            default_role_id = None
        before = {
            "mfa_policy": organization.mfa_policy,
            "password_expiration_days": organization.password_expiration_days,
            "session_timeout_minutes": organization.session_timeout_minutes,
            "allow_api_access": organization.allow_api_access,
            "timezone": organization.timezone,
            "date_format": organization.date_format,
            "default_role_id": organization.default_role_id,
        }
        organization.mfa_policy = mfa_policy
        organization.password_expiration_days = password_expiration_days
        organization.session_timeout_minutes = session_timeout_minutes
        organization.allow_api_access = bool(allow_api_access)
        organization.timezone = timezone_name
        organization.date_format = date_format
        organization.default_role_id = default_role_id
        if mfa_policy == "required":
            for user in organization.users:
                if user.deleted_at is None:
                    user.mfa_required = True
        self.audit.record(
            "organization.settings.update", "organization", organization.id,
            "Updated security and default settings", module="administration",
            organization_id=organization.id,
            event_data={"before": before, "after": {
                "mfa_policy": organization.mfa_policy,
                "password_expiration_days": organization.password_expiration_days,
                "session_timeout_minutes": organization.session_timeout_minutes,
                "allow_api_access": organization.allow_api_access,
                "timezone": organization.timezone,
                "date_format": organization.date_format,
                "default_role_id": organization.default_role_id,
            }},
        )
        return organization

    def available_default_roles(self, organization: Organization) -> list[Role]:
        self._require_staff()
        return list(self.db.scalars(
            select(Role).where(
                or_(Role.organization_id.is_(None), Role.organization_id == organization.id)
            ).order_by(Role.is_system.desc(), Role.name.asc())
        ))

    def _replace_modules(self, organization: Organization, requested: set[str]) -> None:
        assignments = {item.module_slug: item for item in organization.modules}
        for module in module_registry.enabled():
            assignment = assignments.get(module.slug)
            enabled = module.slug in requested
            if assignment is None:
                assignment = OrganizationModule(
                    organization=organization,
                    module_slug=module.slug,
                    enabled=enabled,
                )
                self.db.add(assignment)
            else:
                assignment.enabled = enabled
        self.db.flush()

    def audit_logs(self, organization_id: int, limit: int = 50) -> list[AuditLog]:
        self._require_staff()
        return list(self.db.scalars(select(AuditLog).where(AuditLog.organization_id == int(organization_id)).order_by(AuditLog.created_at.desc()).limit(max(1, min(limit, 250)))))

    def _name_free(self, name: str, exclude_id: int | None = None) -> None:
        statement = select(Organization.id).where(func.lower(Organization.name) == name.lower())
        if exclude_id is not None:
            statement = statement.where(Organization.id != exclude_id)
        if self.db.scalar(statement) is not None:
            raise HTTPException(409, "An organization with that name already exists")

    def _unique_slug(self, name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "organization"
        candidate = base
        counter = 2
        while self.db.scalar(select(Organization.id).where(Organization.slug == candidate)) is not None:
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    @staticmethod
    def _name(value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not 2 <= len(normalized) <= 120:
            raise HTTPException(400, "Organization name must be between 2 and 120 characters")
        return normalized

    @staticmethod
    def _optional_name(value: str) -> str | None:
        normalized = " ".join(value.strip().split())
        if len(normalized) > 120:
            raise HTTPException(400, "Display name must be 120 characters or fewer")
        return normalized or None

    @staticmethod
    def _type(value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in Organization.ALLOWED_TYPES:
            raise HTTPException(400, "Organization type must be staff or reseller")
        return normalized

    @classmethod
    def _status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in cls.ALLOWED_STATUSES:
            raise HTTPException(400, "Invalid organization status")
        return normalized
