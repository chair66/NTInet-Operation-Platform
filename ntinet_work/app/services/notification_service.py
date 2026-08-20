from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from sqlalchemy.orm import Session

from app.database.models import NotificationEvent
from app.security.context import SecurityContext


@dataclass(slots=True)
class NotificationService:
    """Transactional notification outbox.

    PLAT-003B.4 stores events for future email, Slack, Teams, SMS, or web delivery.
    Delivery workers are intentionally outside this milestone.
    """

    db: Session
    context: SecurityContext | None = None

    def publish(
        self,
        event_type: str,
        *,
        subject: str = "",
        payload: dict[str, Any] | None = None,
        recipient_user_id: int | None = None,
        organization_id: int | None = None,
        channel: str = "internal",
    ) -> NotificationEvent:
        actor = self.context.user if self.context else None
        event = NotificationEvent(
            organization_id=organization_id if organization_id is not None else getattr(actor, "organization_id", None),
            actor_user_id=getattr(actor, "id", None),
            recipient_user_id=recipient_user_id,
            event_type=event_type.strip(),
            channel=channel.strip() or "internal",
            subject=subject.strip(),
            payload=json.dumps(payload or {}, sort_keys=True, default=str),
            status="pending",
        )
        self.db.add(event)
        return event
