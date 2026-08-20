from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Permission, Role, User
from app.security.context import SecurityContext
from app.security.scopes import scope_roles, validate_role_assignment


@dataclass(slots=True)
class RoleService:
    db: Session
    context: SecurityContext

    def list_visible(self) -> list[Role]:
        return list(self.db.scalars(scope_roles(select(Role).order_by(Role.name), self.context)).unique())

    def get_visible(self, role_id: int) -> Role:
        role = self.db.scalar(scope_roles(select(Role).where(Role.id == int(role_id)), self.context))
        if not role: raise HTTPException(404, "Role not found")
        return role

    def resolve_assignable(self, role_ids: Iterable[int], target_organization_id: int) -> list[Role]:
        ids = sorted({int(v) for v in role_ids})
        if not ids: return []
        roles = list(self.db.scalars(select(Role).where(Role.id.in_(ids))).unique())
        if len(roles) != len(ids): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more roles were not found")
        return validate_role_assignment(self.context, target_organization_id, roles)

    def assign(self, user: User, role_ids: Iterable[int]) -> list[Role]:
        roles = self.resolve_assignable(role_ids, user.organization_id); user.roles = roles; return roles

    @staticmethod
    def effective_permissions(user: User) -> frozenset[str]: return frozenset(user.permissions)

    @staticmethod
    def permissions_by_module(user: User) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for key in sorted(user.permissions):
            module = key.split(".", 1)[0] if "." in key else "general"
            grouped[module].append(key)
        return dict(grouped)

    @staticmethod
    def role_permissions_by_module(role: Role) -> dict[str, list[Permission]]:
        grouped: dict[str, list[Permission]] = defaultdict(list)
        for permission in sorted(role.permissions, key=lambda p: p.key):
            grouped[permission.key.split(".", 1)[0] if "." in permission.key else "general"].append(permission)
        return dict(grouped)
