from __future__ import annotations

from dataclasses import dataclass

from app.database.models import Organization, User


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Immutable request security information."""

    user: User
    organization: Organization
    permissions: frozenset[str]
    module_slugs: frozenset[str]
    role_names: frozenset[str]

    @classmethod
    def from_user(cls, user: User) -> "SecurityContext":
        organization = user.organization
        module_slugs = frozenset(
            assignment.module_slug
            for assignment in organization.modules
            if assignment.enabled
        )
        role_names = frozenset(role.name for role in user.roles)
        return cls(
            user=user,
            organization=organization,
            permissions=frozenset(user.permissions),
            module_slugs=module_slugs,
            role_names=role_names,
        )

    @property
    def user_id(self) -> int:
        return self.user.id

    @property
    def organization_id(self) -> int:
        return self.organization.id

    @property
    def is_superuser(self) -> bool:
        return self.user.is_superuser

    @property
    def is_staff(self) -> bool:
        return self.organization.is_staff

    @property
    def is_reseller(self) -> bool:
        return self.organization.is_reseller

    def can(self, permission: str) -> bool:
        return self.is_superuser or "*" in self.permissions or permission in self.permissions

    def has_module_assignment(self, module_slug: str) -> bool:
        return self.is_superuser or module_slug in self.module_slugs
