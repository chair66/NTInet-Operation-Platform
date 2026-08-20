from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.models import (
    AuditLog,
    NotificationEvent,
    Organization,
    OrganizationModule,
    Permission,
    Role,
    User,
)
from app.modules.registry import module_registry, register_builtin_modules
from app.security.passwords import hash_password


PERMISSIONS = {
    "dashboard.read": "View the dashboard",
    "numbers.read": "View telephone numbers",
    "numbers.buy": "Search and purchase telephone numbers",
    "numbers.move": "Move telephone numbers between locations",
    "numbers.features": "Change routing and line features",
    "ports.read": "View port orders",
    "ports.create": "Create port orders",
    "ports.manage": "Update or cancel port orders",
    "csr.read": "View CSR orders",
    "csr.create": "Create CSR orders",
    "digicloud.view": "Access DigiCloud",
    "nti_mobile.view": "Access NTI Mobile",
    "nti_mobile.dashboard": "View the NTI Mobile dashboard",
    "nti_mobile.orders.read": "View NTI Mobile orders",
    "nti_mobile.orders.create": "Create NTI Mobile orders",
    "nti_mobile.orders.manage": "Manage NTI Mobile orders",
    "nti_mobile.customers.read": "View NTI Mobile customers",
    "nti_mobile.customers.manage": "Manage NTI Mobile customers",
    "nti_mobile.lines.read": "View NTI Mobile lines",
    "nti_mobile.lines.manage": "Manage NTI Mobile lines",
    "nti_mobile.sims.read": "View NTI Mobile SIM inventory",
    "nti_mobile.sims.manage": "Manage NTI Mobile SIM inventory",
    "nti_mobile.numbers.read": "View NTI Mobile phone numbers",
    "nti_mobile.numbers.manage": "Manage NTI Mobile phone numbers",
    "nti_mobile.plans.read": "View NTI Mobile plans",
    "nti_mobile.plans.manage": "Manage NTI Mobile plans",
    "nti_mobile.ports.read": "View NTI Mobile port requests",
    "nti_mobile.ports.create": "Create NTI Mobile port requests",
    "nti_mobile.ports.manage": "Manage NTI Mobile port requests",
    "nti_mobile.exceptions.read": "View NTI Mobile exceptions",
    "nti_mobile.exceptions.manage": "Manage NTI Mobile exceptions",
    "nti_mobile.settings": "Manage NTI Mobile settings",
    "reports.view": "View reports",
    "admin.api_logs": "View API diagnostics",
    "admin.users": "Manage users",
    "admin.organizations": "Manage organizations",
    "admin.roles": "Manage roles and permissions",
    "admin.modules": "Manage organization module access",
    "admin.audit": "View audit history",
}

ROLE_MAP = {
    "Operations Admin": list(PERMISSIONS),
    "Support": [
        "dashboard.read",
        "numbers.read",
        "numbers.move",
        "numbers.features",
        "ports.read",
        "ports.create",
        "csr.read",
        "csr.create",
        "nti_mobile.view",
        "nti_mobile.dashboard",
        "nti_mobile.orders.read",
        "nti_mobile.customers.read",
        "nti_mobile.lines.read",
        "nti_mobile.lines.manage",
        "nti_mobile.sims.read",
        "nti_mobile.sims.manage",
        "nti_mobile.numbers.read",
        "nti_mobile.ports.read",
        "nti_mobile.ports.create",
        "nti_mobile.exceptions.read",
    ],
    "Sales": [
        "dashboard.read",
        "numbers.read",
        "numbers.buy",
        "ports.read",
        "nti_mobile.view",
        "nti_mobile.dashboard",
        "nti_mobile.orders.read",
        "nti_mobile.orders.create",
        "nti_mobile.customers.read",
        "nti_mobile.customers.manage",
        "nti_mobile.plans.read",
        "nti_mobile.ports.read",
        "nti_mobile.ports.create",
    ],
    "Read Only": [
        "dashboard.read",
        "numbers.read",
        "ports.read",
        "csr.read",
        "nti_mobile.view",
        "nti_mobile.dashboard",
        "nti_mobile.orders.read",
        "nti_mobile.customers.read",
        "nti_mobile.lines.read",
        "nti_mobile.sims.read",
        "nti_mobile.numbers.read",
        "nti_mobile.plans.read",
        "nti_mobile.ports.read",
        "nti_mobile.exceptions.read",
    ],
    "Reseller Admin": [
        "dashboard.read",
        "numbers.read",
        "numbers.buy",
        "numbers.move",
        "numbers.features",
        "ports.read",
        "ports.create",
        "csr.read",
        "csr.create",
        "admin.users",
    ],
    "Reseller Technician": [
        "dashboard.read",
        "numbers.read",
        "numbers.move",
        "numbers.features",
        "ports.read",
        "ports.create",
    ],
    "Reseller Sales": [
        "dashboard.read",
        "numbers.read",
        "numbers.buy",
        "ports.read",
    ],
}


def _remove_legacy_empty_staff_duplicates(
    db: Session,
    canonical: Organization,
) -> None:
    """Remove known empty staff seed records left by early development builds."""

    legacy_names = {"ntinet staff", "digicloud / ntinet"}
    legacy_slugs = {"digicloud", "ntinet-staff", "ntinet_staff"}

    candidates = db.scalars(
        select(Organization).where(
            Organization.id != canonical.id,
            Organization.organization_type == Organization.STAFF_TYPE,
        )
    ).all()

    for duplicate in candidates:
        normalized_name = (duplicate.name or "").strip().lower()
        normalized_slug = (duplicate.slug or "").strip().lower()

        if (
            normalized_name not in legacy_names
            and normalized_slug not in legacy_slugs
        ):
            continue

        user_count = int(
            db.scalar(
                select(func.count(User.id)).where(
                    User.organization_id == duplicate.id
                )
            )
            or 0
        )

        if user_count:
            continue

        db.execute(
            update(AuditLog)
            .where(AuditLog.organization_id == duplicate.id)
            .values(organization_id=canonical.id)
        )
        db.execute(
            update(NotificationEvent)
            .where(NotificationEvent.organization_id == duplicate.id)
            .values(organization_id=canonical.id)
        )
        db.execute(
            delete(Role).where(Role.organization_id == duplicate.id)
        )
        db.delete(duplicate)
        db.flush()


def seed_staff_organization(db: Session) -> Organization:
    settings = get_settings()

    organization = db.scalar(
        select(Organization).where(Organization.slug == "ntinet")
    )

    if organization is None:
        organization = db.scalar(
            select(Organization).where(
                func.lower(Organization.name) == "ntinet"
            )
        )

    if organization is None:
        organization = db.scalar(
            select(Organization)
            .join(User, User.organization_id == Organization.id)
            .where(
                Organization.organization_type == Organization.STAFF_TYPE
            )
            .group_by(Organization.id)
            .order_by(
                func.count(User.id).desc(),
                Organization.id.asc(),
            )
        )

    if organization is None:
        organization = db.scalar(
            select(Organization)
            .where(
                Organization.organization_type == Organization.STAFF_TYPE
            )
            .order_by(Organization.id.asc())
        )

    if organization is None:
        organization = Organization(
            name="NTInet",
            slug="ntinet",
            organization_type="staff",
            bandwidth_account_id=settings.bandwidth_account_id,
            active=True,
            is_protected=True,
        )
        db.add(organization)
        db.flush()
    else:
        organization.name = "NTInet"
        organization.slug = "ntinet"
        organization.organization_type = "staff"
        organization.active = True
        organization.is_protected = True

        if not organization.bandwidth_account_id:
            organization.bandwidth_account_id = settings.bandwidth_account_id

    db.execute(
        update(Organization)
        .where(
            Organization.id != organization.id,
            Organization.is_protected.is_(True),
        )
        .values(is_protected=False)
    )

    _remove_legacy_empty_staff_duplicates(db, organization)
    return organization


def seed_permissions(db: Session) -> dict[str, Permission]:
    permission_objects: dict[str, Permission] = {}

    for key, description in PERMISSIONS.items():
        permission = db.scalar(
            select(Permission).where(Permission.key == key)
        )

        if permission is None:
            permission = Permission(
                key=key,
                description=description,
            )
            db.add(permission)
            db.flush()
        else:
            permission.description = description

        permission_objects[key] = permission

    return permission_objects


def seed_roles(
    db: Session,
    permission_objects: dict[str, Permission],
) -> None:
    for name, permission_keys in ROLE_MAP.items():
        role = db.scalar(
            select(Role).where(
                Role.name == name,
                Role.organization_id.is_(None),
            )
        )

        if role is None:
            role = Role(
                name=name,
                description=f"Built-in {name} role",
                organization_id=None,
                is_system=True,
            )
            db.add(role)
            db.flush()

        role.permissions = [
            permission_objects[key]
            for key in permission_keys
        ]


def seed_staff_modules(
    db: Session,
    organization: Organization,
) -> None:
    register_builtin_modules()
    enabled_slugs = {
        module.slug
        for module in module_registry.enabled()
    }

    db.execute(
        delete(OrganizationModule).where(
            OrganizationModule.module_slug.not_in(enabled_slugs)
        )
    )

    for module in module_registry.enabled():
        assignment = db.scalar(
            select(OrganizationModule).where(
                OrganizationModule.organization_id == organization.id,
                OrganizationModule.module_slug == module.slug,
            )
        )

        if assignment is None:
            db.add(
                OrganizationModule(
                    organization_id=organization.id,
                    module_slug=module.slug,
                    enabled=True,
                )
            )
        else:
            assignment.enabled = True


def seed_admin(
    db: Session,
    organization: Organization,
) -> None:
    settings = get_settings()
    email = settings.bootstrap_admin_email.lower()
    admin = db.scalar(
        select(User).where(User.email == email)
    )

    if admin is None:
        db.add(
            User(
                email=email,
                full_name=settings.bootstrap_admin_name,
                password_hash=hash_password(
                    settings.bootstrap_admin_password
                ),
                organization_id=organization.id,
                is_superuser=True,
            )
        )
    else:
        admin.organization_id = organization.id


def seed_database(db: Session) -> None:
    organization = seed_staff_organization(db)
    permissions = seed_permissions(db)
    seed_roles(db, permissions)
    seed_staff_modules(db, organization)
    seed_admin(db, organization)
    db.commit()
