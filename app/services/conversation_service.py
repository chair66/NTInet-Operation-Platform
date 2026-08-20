from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, noload, selectinload

from app.database.customer_communication_models import CommunicationConversation, CustomerCommunication
from app.database.models import User
from app.security.context import SecurityContext


CONVERSATION_STATUSES = {"open", "waiting_on_customer", "closed"}


def normalized_subject(value: str) -> str:
    return re.sub(r"^\s*((re|fw|fwd)\s*:\s*)+", "", value or "", flags=re.I).strip().lower()


def display_subject(value: str) -> str:
    return re.sub(r"^\s*((re|fw|fwd)\s*:\s*)+", "", value or "", flags=re.I).strip()


def conversation_key(message: CustomerCommunication) -> str:
    if message.ticket_id:
        return f"ticket-{message.ticket_id}:{message.channel}"
    if message.estimate_id:
        return f"estimate-{message.estimate_id}:{message.channel}:{message.contact_id or 0}"
    if message.channel == "email":
        digest = hashlib.sha256(normalized_subject(message.subject).encode()).hexdigest()[:20]
        return f"customer-{message.customer_id}:email:{message.contact_id or 0}:{digest}"
    return f"customer-{message.customer_id}:sms:{message.contact_id or 0}"


@dataclass(slots=True)
class ConversationService:
    db: Session
    context: SecurityContext | None = None

    def _scope(self, statement):
        if self.context and not self.context.is_staff:
            statement = statement.where(CommunicationConversation.organization_id == self.context.organization_id)
        return statement

    def list(self, *, customer_id: int | None = None, status: str = "", channel: str = "",
             assignment: str = "", query: str = "", limit: int = 200) -> list[CommunicationConversation]:
        statement = select(CommunicationConversation).options(
            selectinload(CommunicationConversation.messages).options(
                joinedload(CustomerCommunication.contact),
                joinedload(CustomerCommunication.created_by),
                noload(CustomerCommunication.customer),
                noload(CustomerCommunication.ticket),
                noload(CustomerCommunication.estimate),
                noload(CustomerCommunication.organization),
                noload(CustomerCommunication.communication_profile),
            ),
            selectinload(CommunicationConversation.ticket),
            selectinload(CommunicationConversation.estimate),
        )
        statement = self._scope(statement)
        if customer_id:
            statement = statement.where(CommunicationConversation.customer_id == customer_id)
        if status in CONVERSATION_STATUSES:
            statement = statement.where(CommunicationConversation.status == status)
        elif status == "unread":
            statement = statement.where(CommunicationConversation.unread_count > 0)
        if channel in {"sms", "email"}:
            statement = statement.where(CommunicationConversation.channel == channel)
        if assignment == "mine" and self.context:
            statement = statement.where(CommunicationConversation.assigned_user_id == self.context.user_id)
        elif assignment == "unassigned":
            statement = statement.where(CommunicationConversation.assigned_user_id.is_(None))
        conversations = list(self.db.scalars(statement.order_by(
            CommunicationConversation.last_message_at.desc()).limit(max(1, min(limit, 500)))).unique())
        if query.strip():
            needle = query.strip().lower()
            conversations = [item for item in conversations if needle in " ".join((
                item.customer.name, item.customer.customer_number,
                item.contact.full_name if item.contact else "",
                item.contact.email if item.contact else "",
                item.contact.mobile_phone if item.contact else "",
                item.subject, item.last_message_preview,
                item.ticket.ticket_number if item.ticket else "",
            )).lower()]
        return conversations

    def get(self, conversation_id: int) -> CommunicationConversation | None:
        return self.db.scalar(self._scope(select(CommunicationConversation).where(
            CommunicationConversation.id == conversation_id)))

    def attach(self, message: CustomerCommunication, conversation_id: int | None = None) -> CommunicationConversation:
        conversation = self.db.get(CommunicationConversation, conversation_id) if conversation_id else None
        if conversation and (conversation.customer_id != message.customer_id or conversation.channel != message.channel):
            raise ValueError("The communication does not belong to the selected conversation.")
        key = conversation.thread_key if conversation else conversation_key(message)
        if not conversation:
            # Attaching a message only needs the conversation row.  The model's
            # select-in messages relationship otherwise fires immediately and
            # each CustomerCommunication's joined relationships can expand into
            # the full ticket/job/estimate graph.  PostgreSQL rejects that
            # generated SELECT once it exceeds its 1,664-column target-list
            # limit.  Suppress message loading for this focused lookup.
            conversation = self.db.scalar(
                select(CommunicationConversation)
                .options(noload(CommunicationConversation.messages))
                .where(CommunicationConversation.thread_key == key)
            )
        now = message.received_at or message.sent_at or message.created_at or datetime.now(timezone.utc)
        if not conversation:
            conversation = CommunicationConversation(
                organization_id=message.organization_id, customer_id=message.customer_id,
                contact_id=message.contact_id, ticket_id=message.ticket_id,
                estimate_id=message.estimate_id,
                communication_profile_id=message.communication_profile_id,
                channel=message.channel, subject=display_subject(message.subject) if message.channel == "email" else "",
                thread_key=key, status="open", unread_count=0,
                last_message_preview=message.body[:255], last_direction=message.direction,
                last_message_at=now,
            )
            self.db.add(conversation); self.db.flush()
        message.conversation_id = conversation.id
        message.thread_key = key
        message.is_read = message.direction != "inbound"
        message.read_at = now if message.is_read else None
        conversation.contact_id = message.contact_id or conversation.contact_id
        conversation.ticket_id = message.ticket_id or conversation.ticket_id
        conversation.estimate_id = message.estimate_id or conversation.estimate_id
        conversation.communication_profile_id = message.communication_profile_id or conversation.communication_profile_id
        conversation.last_message_preview = message.body[:255]
        conversation.last_direction = message.direction
        conversation.last_message_at = now
        if message.direction == "inbound":
            conversation.unread_count += 1
            conversation.status = "open"
        elif conversation.status == "open":
            conversation.status = "waiting_on_customer"
        return conversation

    def mark_read(self, conversation: CommunicationConversation) -> None:
        now = datetime.now(timezone.utc)
        for message in conversation.messages:
            if not message.is_read:
                message.is_read = True; message.read_at = now
        conversation.unread_count = 0

    def set_status(self, conversation: CommunicationConversation, status: str) -> None:
        if status not in CONVERSATION_STATUSES:
            raise ValueError("Invalid conversation status.")
        conversation.status = status
        conversation.closed_at = datetime.now(timezone.utc) if status == "closed" else None

    def assign(self, conversation: CommunicationConversation, user_id: int | None) -> None:
        if user_id is None:
            conversation.assigned_user_id = None; return
        user = self.db.scalar(select(User).where(User.id == user_id, User.active.is_(True)))
        if not user:
            raise ValueError("Selected assignee is not active.")
        if self.context and not self.context.is_staff and user.organization_id != self.context.organization_id:
            raise ValueError("The selected assignee is outside your organization.")
        conversation.assigned_user_id = user.id

    def link_ticket(self, conversation: CommunicationConversation, ticket_id: int | None) -> None:
        conversation.ticket_id = ticket_id
        for message in conversation.messages:
            message.ticket_id = ticket_id

    def available_assignees(self) -> list[User]:
        statement = select(User).where(User.active.is_(True))
        if self.context and not self.context.is_staff:
            statement = statement.where(User.organization_id == self.context.organization_id)
        return list(self.db.scalars(statement.order_by(User.full_name)).unique())
