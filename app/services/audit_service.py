from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any

from fastapi import Request
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.database.models import AuditLog, Organization, User
from app.security.context import SecurityContext
from app.security.scopes import scope_audit_logs


@dataclass(slots=True)
class AuditService:
    db: Session
    request: Request | None = None
    actor_context: SecurityContext | None = None

    def record(self, action: str, resource_type: str = "", resource_id: str | int = "", detail: str = "", *, module: str = "", event_data: dict[str, Any] | None = None, user_id: int | None = None, organization_id: int | None = None, ip_address: str | None = None) -> AuditLog:
        actor = self.actor_context.user if self.actor_context else None
        resolved_ip = ip_address
        if resolved_ip is None and self.request is not None and self.request.client is not None:
            resolved_ip = self.request.client.host
        entry = AuditLog(
            user_id=user_id if user_id is not None else getattr(actor, "id", None),
            organization_id=organization_id if organization_id is not None else getattr(actor, "organization_id", None),
            action=action.strip(), resource_type=resource_type.strip(), resource_id=str(resource_id or ""), detail=detail.strip(),
            module=(module or (action.split(".", 1)[0] if "." in action else resource_type)).strip(),
            event_data=json.dumps(event_data or {}, sort_keys=True, default=str), ip_address=resolved_ip or "",
        )
        self.db.add(entry)
        return entry

    def list_recent(self, context: SecurityContext, limit: int = 250) -> list[AuditLog]:
        return self.search(context, limit=limit)

    def search(self, context: SecurityContext, *, query: str = "", action: str = "", module: str = "", organization_id: int | None = None, date_from: datetime | None = None, date_to: datetime | None = None, limit: int = 250) -> list[AuditLog]:
        safe_limit = max(1, min(int(limit), 2000))
        statement: Select = select(AuditLog).outerjoin(AuditLog.user)
        statement = scope_audit_logs(statement, context)
        if query.strip():
            term = f"%{query.strip().lower()}%"
            statement = statement.where(or_(func.lower(AuditLog.action).like(term), func.lower(AuditLog.detail).like(term), func.lower(AuditLog.resource_type).like(term), func.lower(AuditLog.resource_id).like(term), func.lower(AuditLog.ip_address).like(term), func.lower(User.full_name).like(term), func.lower(User.email).like(term)))
        if action.strip(): statement = statement.where(AuditLog.action == action.strip())
        if module.strip(): statement = statement.where(AuditLog.module == module.strip())
        if organization_id is not None:
            if not (context.is_staff and context.is_superuser) and int(organization_id) != context.organization_id:
                return []
            statement = statement.where(AuditLog.organization_id == int(organization_id))
        if date_from is not None: statement = statement.where(AuditLog.created_at >= date_from)
        if date_to is not None: statement = statement.where(AuditLog.created_at <= date_to)
        return list(self.db.scalars(statement.order_by(AuditLog.created_at.desc()).limit(safe_limit)).unique())

    def filter_options(self, context: SecurityContext) -> tuple[list[str], list[str], list[Organization]]:
        scoped = scope_audit_logs(select(AuditLog), context).subquery()
        actions = [v for v in self.db.scalars(select(scoped.c.action).distinct().order_by(scoped.c.action)) if v]
        modules = [v for v in self.db.scalars(select(scoped.c.module).distinct().order_by(scoped.c.module)) if v]
        orgs = list(self.db.scalars(select(Organization).order_by(Organization.name))) if context.is_staff and context.is_superuser else [context.organization]
        return actions, modules, orgs
