from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email import message_from_bytes, policy
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.communication_models import CommunicationProfile
from app.database.customer_communication_models import (
    CommunicationConversation,
    CustomerCommunication,
    InboundEmailImport,
)
from app.database.customer_models import Customer, CustomerContact
from app.database.models import NotificationEvent, User
from app.database.ticket_models import TicketEntry, TicketOutboundMessage
from app.services.conversation_service import ConversationService
from app.services.notification_service import NotificationService
from app.services.notifications import send_email


settings = get_settings()


def _header(value: object) -> str:
    return str(value or "").strip()


def _message_ids(value: str) -> list[str]:
    return re.findall(r"<[^>]+>", value or "")


def _received_at(message: Message) -> datetime:
    try:
        value = parsedate_to_datetime(_header(message.get("Date")))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value
    except (TypeError, ValueError, OverflowError):
        return datetime.now(timezone.utc)


def _plain_body(message: Message) -> str:
    if message.is_multipart():
        plain = []
        html_parts = []
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type not in {"text/plain", "text/html"}:
                continue
            try:
                content = part.get_content()
            except (LookupError, UnicodeDecodeError):
                payload = part.get_payload(decode=True) or b""
                content = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            (plain if content_type == "text/plain" else html_parts).append(str(content))
        if plain:
            return "\n".join(plain).strip()
        source = "\n".join(html_parts)
    else:
        try:
            source = str(message.get_content())
        except (LookupError, UnicodeDecodeError):
            source = (message.get_payload(decode=True) or b"").decode(
                message.get_content_charset() or "utf-8", errors="replace")
        if message.get_content_type() == "text/plain":
            return source.strip()
    source = re.sub(r"<(br|/p|/div|/li)\b[^>]*>", "\n", source, flags=re.I)
    source = re.sub(r"<[^>]+>", " ", source)
    source = html.unescape(source)
    return re.sub(r"\n{3,}", "\n\n", source).strip()


@dataclass(slots=True)
class InboundEmailService:
    db: Session

    def ingest_bytes(self, profile: CommunicationProfile, *, uidvalidity: str,
                     imap_uid: int, raw_message: bytes) -> InboundEmailImport:
        existing = self.db.scalar(select(InboundEmailImport).where(
            InboundEmailImport.communication_profile_id == profile.id,
            InboundEmailImport.uidvalidity == uidvalidity,
            InboundEmailImport.imap_uid == imap_uid,
        ))
        if existing:
            return existing

        parsed = message_from_bytes(raw_message, policy=policy.default)
        message_id = _header(parsed.get("Message-ID"))
        sender = parseaddr(_header(parsed.get("From")))[1].strip().lower()
        subject = _header(parsed.get("Subject"))[:255]
        received_at = _received_at(parsed)
        imported = InboundEmailImport(
            communication_profile_id=profile.id, uidvalidity=uidvalidity,
            imap_uid=imap_uid, email_message_id=message_id,
            sender_address=sender, subject=subject,
            received_at=received_at,
        )
        self.db.add(imported); self.db.flush()

        if message_id:
            duplicate = self.db.scalar(select(CustomerCommunication).where(
                CustomerCommunication.email_message_id == message_id))
            if duplicate:
                imported.customer_communication_id = duplicate.id
                imported.processing_status = "duplicate"
                return imported

        references = _message_ids(
            f"{_header(parsed.get('In-Reply-To'))} {_header(parsed.get('References'))}"
        )
        prior_customer = self.db.scalar(select(CustomerCommunication).where(
            CustomerCommunication.email_message_id.in_(references)
        ).order_by(CustomerCommunication.created_at.desc())) if references else None
        prior_ticket = self.db.scalar(select(TicketOutboundMessage).where(
            TicketOutboundMessage.provider_message_id.in_(references)
        ).order_by(TicketOutboundMessage.created_at.desc())) if references else None

        customer = prior_customer.customer if prior_customer else (prior_ticket.ticket.customer if prior_ticket else None)
        contact = prior_customer.contact if prior_customer else (prior_ticket.contact if prior_ticket else None)
        ticket_id = prior_customer.ticket_id if prior_customer else (prior_ticket.ticket_id if prior_ticket else None)
        estimate_id = prior_customer.estimate_id if prior_customer else None
        explicit_conversation_id = prior_customer.conversation_id if prior_customer else None

        if not customer and sender:
            candidates = list(self.db.scalars(select(CustomerContact).where(
                CustomerContact.active.is_(True), func.lower(CustomerContact.email) == sender)).unique())
            preferred = [item for item in candidates if item.customer.owner_organization_id == profile.organization_id
                         or item.customer.servicing_organization_id == profile.organization_id]
            matches = preferred if len(preferred) == 1 else candidates
            if len(matches) == 1:
                contact = matches[0]; customer = contact.customer
        if not customer:
            imported.processing_status = "unmatched"
            imported.error_message = "No unique customer contact matched the sender or reply headers."
            return imported

        body = _plain_body(parsed)
        communication = CustomerCommunication(
            customer_id=customer.id, contact_id=contact.id if contact else None,
            ticket_id=ticket_id,
            estimate_id=estimate_id,
            organization_id=customer.servicing_organization_id or customer.owner_organization_id,
            communication_profile_id=profile.id,
            direction="inbound", channel="email", subject=subject,
            body=body or "(Message contained no readable text.)",
            source_address=sender, destination_address=profile.sender_address or profile.imap_username,
            profile_name=profile.name, provider="imap",
            provider_message_id=message_id, email_message_id=message_id,
            email_in_reply_to=_header(parsed.get("In-Reply-To")),
            email_references=_header(parsed.get("References")),
            status="received", received_at=received_at, is_read=False,
        )
        self.db.add(communication); self.db.flush()
        conversation = ConversationService(self.db).attach(communication, explicit_conversation_id)
        imported.customer_communication_id = communication.id
        imported.processing_status = "processed"

        if conversation.ticket_id:
            ticket_id = conversation.ticket_id
            communication.ticket_id = ticket_id
            self.db.add(TicketEntry(
                ticket_id=ticket_id, entry_type="customer_reply", visibility="customer",
                body=(f"Customer email reply from {contact.full_name if contact else sender} <{sender}>\n"
                      f"Subject: {subject}\n\n{communication.body}"),
            ))
        self._notify(conversation, communication)
        return imported

    def _notify(self, conversation: CommunicationConversation,
                communication: CustomerCommunication) -> None:
        recipients: list[User] = []
        if conversation.assigned_user and conversation.assigned_user.active:
            recipients = [conversation.assigned_user]
        elif conversation.ticket and conversation.ticket.assigned_user and conversation.ticket.assigned_user.active:
            recipients = [conversation.ticket.assigned_user]
        else:
            users = list(self.db.scalars(select(User).where(
                User.organization_id == conversation.organization_id,
                User.active.is_(True), User.deleted_at.is_(None),
            )).unique())
            recipients = [user for user in users if user.can("customer_communications.read") or user.can("tickets.read")]

        target = f"/communications#conversation-{conversation.id}"
        ticket_number = conversation.ticket.ticket_number if conversation.ticket else ""
        notification_subject = (
            f"Customer Reply: [{ticket_number}] {conversation.subject or communication.subject}"
            if ticket_number else f"Customer Email Reply: {conversation.customer.name}"
        )
        notification_body = (
            f"{conversation.contact.full_name if conversation.contact else communication.source_address} replied by email.\n\n"
            f"Customer: {conversation.customer.name}\nSubject: {communication.subject}\n\n"
            f"{communication.body[:1200]}\n\n"
            f"Open conversation: {settings.ticket_public_base_url.rstrip('/')}{target}"
        )
        for recipient in recipients:
            if recipient.email.strip().lower() == communication.source_address.strip().lower():
                continue
            NotificationService(self.db).publish(
                "communications.customer_email_reply", subject=notification_subject,
                payload={"conversation_id": conversation.id, "communication_id": communication.id,
                         "ticket_id": conversation.ticket_id, "customer_id": conversation.customer_id},
                recipient_user_id=recipient.id, organization_id=recipient.organization_id,
                channel="internal", target_url=target,
            )
            result = send_email(notification_subject, notification_body, [recipient.email])
            event = NotificationService(self.db).publish(
                "communications.customer_email_reply", subject=notification_subject,
                payload={"conversation_id": conversation.id, "recipient": recipient.email,
                         "delivery_message": result.message},
                recipient_user_id=recipient.id, organization_id=recipient.organization_id,
                channel="email", target_url=target,
            )
            event.status = "sent" if result.ok else "failed"
            event.processed_at = datetime.now(timezone.utc)
