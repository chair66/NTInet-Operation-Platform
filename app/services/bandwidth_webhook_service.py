from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.communication_models import CommunicationProfile
from app.database.customer_communication_models import (
    BandwidthMessagingWebhookEvent,
    CustomerCommunication,
)
from app.database.customer_models import Customer, CustomerContact
from app.database.models import User
from app.database.ticket_models import Ticket, TicketEntry, TicketOutboundMessage
from app.services.notification_service import NotificationService
from app.services.ticket_communications import normalize_us_number
from app.services.conversation_service import ConversationService


OUTBOUND_STATUS = {
    "message-sending": "sending",
    "message-sent": "sent",
    "message-delivered": "delivered",
    "message-failed": "failed",
}
STOP_WORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}
START_WORDS = {"START", "UNSTOP"}


def _event_time(value: object) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


@dataclass(slots=True)
class BandwidthWebhookService:
    db: Session

    def process_batch(self, payload: object) -> list[BandwidthMessagingWebhookEvent]:
        if not isinstance(payload, list):
            raise ValueError("Bandwidth Messaging callbacks must be a JSON array.")
        results = []
        for item in payload:
            if isinstance(item, dict):
                results.append(self.process(item))
        return results

    def process(self, item: dict) -> BandwidthMessagingWebhookEvent:
        message = item.get("message") if isinstance(item.get("message"), dict) else {}
        event_type = str(item.get("type") or "unknown")
        message_id = str(message.get("id") or "")
        destination = item.get("to") or ((message.get("to") or [""])[0] if isinstance(message.get("to"), list) else message.get("to")) or ""
        source = str(message.get("from") or "")
        canonical = json.dumps(item, sort_keys=True, separators=(",", ":"), default=str)
        dedupe = hashlib.sha256(f"{event_type}|{message_id}|{destination}|{canonical}".encode()).hexdigest()
        existing = self.db.scalar(select(BandwidthMessagingWebhookEvent).where(
            BandwidthMessagingWebhookEvent.deduplication_key == dedupe))
        if existing:
            return existing

        event = BandwidthMessagingWebhookEvent(
            deduplication_key=dedupe, event_type=event_type,
            provider_message_id=message_id,
            application_id=str(message.get("applicationId") or ""),
            source_address=normalize_us_number(source) or source,
            destination_address=normalize_us_number(str(destination)) or str(destination),
            description=str(item.get("description") or ""),
            error_code=str(item.get("errorCode") or ""),
            event_at=_event_time(item.get("time")),
        )
        self.db.add(event); self.db.flush()
        if event_type == "message-received":
            self._receive(event, message)
        elif event_type in OUTBOUND_STATUS:
            self._update_delivery(event)
        else:
            event.processing_status = "ignored"
        return event

    def _update_delivery(self, event: BandwidthMessagingWebhookEvent) -> None:
        customer_message = self.db.scalar(select(CustomerCommunication).where(
            CustomerCommunication.provider_message_id == event.provider_message_id))
        ticket_message = self.db.scalar(select(TicketOutboundMessage).where(
            TicketOutboundMessage.provider_message_id == event.provider_message_id))
        status = OUTBOUND_STATUS[event.event_type]
        when = event.event_at or datetime.now(timezone.utc)
        for record in (customer_message, ticket_message):
            if not record:
                continue
            record.status = status
            record.error_message = event.description if status == "failed" else ""
            if hasattr(record, "delivery_description"):
                record.delivery_description = event.description
                record.provider_error_code = event.error_code
            if status == "delivered": record.delivered_at = when
            if status == "failed": record.failed_at = when
        event.customer_communication_id = customer_message.id if customer_message else None
        event.ticket_outbound_message_id = ticket_message.id if ticket_message else None
        event.processing_status = "processed" if customer_message or ticket_message else "unmatched"

    def _receive(self, event: BandwidthMessagingWebhookEvent, message: dict) -> None:
        source = normalize_us_number(event.source_address)
        destination = normalize_us_number(str(message.get("owner") or event.destination_address))
        profiles = list(self.db.scalars(select(CommunicationProfile).where(
            CommunicationProfile.channel == "sms",
            CommunicationProfile.is_active.is_(True),
            CommunicationProfile.bandwidth_application_id == event.application_id,
        ).order_by(CommunicationProfile.id)).unique())
        profile = next((candidate for candidate in profiles
                        if normalize_us_number(candidate.sender_address) == destination), None)
        if not profile and len(profiles) == 1:
            profile = profiles[0]

        # Correlate using narrow column queries. Loading either full ORM entity
        # here recursively joins ticket/job/estimate relationships and can
        # exceed PostgreSQL's target-column limit.
        prior_customer = self.db.execute(select(
            CustomerCommunication.id,
            CustomerCommunication.customer_id,
            CustomerCommunication.contact_id,
            CustomerCommunication.ticket_id,
            CustomerCommunication.conversation_id,
            CustomerCommunication.created_at,
        ).where(
            CustomerCommunication.channel == "sms",
            CustomerCommunication.direction == "outbound",
            CustomerCommunication.destination_address == source,
            CustomerCommunication.communication_profile_id == (profile.id if profile else -1),
        ).order_by(CustomerCommunication.created_at.desc()).limit(1)).first() if source and profile else None
        prior_ticket = self.db.execute(select(
            TicketOutboundMessage.id,
            TicketOutboundMessage.ticket_id,
            TicketOutboundMessage.contact_id,
            TicketOutboundMessage.created_at,
            Ticket.customer_id,
        ).join(Ticket, Ticket.id == TicketOutboundMessage.ticket_id).where(
            TicketOutboundMessage.channel == "sms",
            TicketOutboundMessage.destination == source,
            TicketOutboundMessage.communication_profile_id == (profile.id if profile else -1),
        ).order_by(TicketOutboundMessage.created_at.desc()).limit(1)).first() if source and profile else None

        # Use the most recent outbound context. An older general customer SMS
        # must not override a newer SMS sent from a ticket.
        use_ticket = bool(prior_ticket and (
            not prior_customer or prior_ticket.created_at >= prior_customer.created_at
        ))
        if use_ticket:
            customer_id = prior_ticket.customer_id
            contact_id = prior_ticket.contact_id
            ticket_id = prior_ticket.ticket_id
            explicit_conversation_id = None
        elif prior_customer:
            customer_id = prior_customer.customer_id
            contact_id = prior_customer.contact_id
            ticket_id = prior_customer.ticket_id
            explicit_conversation_id = prior_customer.conversation_id
        else:
            customer_id = contact_id = ticket_id = explicit_conversation_id = None

        customer = self.db.get(Customer, customer_id) if customer_id else None
        contact = self.db.get(CustomerContact, contact_id) if contact_id else None

        if not customer:
            candidates = list(self.db.scalars(select(CustomerContact).join(Customer).where(
                CustomerContact.active.is_(True),
                or_(Customer.owner_organization_id == (profile.organization_id if profile else -1),
                    Customer.servicing_organization_id == (profile.organization_id if profile else -1)),
            )).unique()) if profile else []
            matches = [candidate for candidate in candidates if normalize_us_number(candidate.mobile_phone) == source]
            if len(matches) == 1:
                contact = matches[0]; customer = contact.customer
        if not customer:
            event.processing_status = "unmatched"
            return

        text = str(message.get("text") or "")
        received = CustomerCommunication(
            customer_id=customer.id, contact_id=contact.id if contact else None,
            ticket_id=ticket_id,
            organization_id=customer.servicing_organization_id or customer.owner_organization_id,
            communication_profile_id=profile.id if profile else None,
            direction="inbound", channel="sms", subject="", body=text,
            source_address=source, destination_address=destination,
            profile_name=profile.name if profile else "Bandwidth inbound",
            provider="bandwidth", provider_message_id=event.provider_message_id,
            status="received", error_message="",
            thread_key=f"customer-{customer.id}:sms:{contact.id if contact else 0}",
            received_at=event.event_at,
        )
        self.db.add(received); self.db.flush()
        conversation = ConversationService(self.db).attach(received, explicit_conversation_id)
        # A general conversation may have been linked to a ticket after the
        # outbound SMS was sent. Preserve that current relationship.
        ticket_id = conversation.ticket_id or ticket_id
        received.ticket_id = ticket_id
        event.customer_communication_id = received.id
        event.ticket_outbound_message_id = prior_ticket.id if use_ticket else None
        event.processing_status = "processed"
        if contact:
            keyword = text.strip().upper()
            if keyword in STOP_WORDS: contact.sms_consent_status = "opted_out"
            elif keyword in START_WORDS: contact.sms_consent_status = "consented"
        if ticket_id:
            self.db.add(TicketEntry(ticket_id=ticket_id, entry_type="customer_reply",
                visibility="customer", body=f"Inbound SMS from {source}:\n{text}"))
        self._notify(conversation, received, ticket_id)

    def _notify(self, conversation, communication: CustomerCommunication,
                ticket_id: int | None) -> None:
        """Create clickable header notifications for an inbound SMS reply."""
        ticket_row = self.db.execute(select(
            Ticket.ticket_number, Ticket.assigned_user_id
        ).where(Ticket.id == ticket_id)).first() if ticket_id else None
        assigned_user_id = conversation.assigned_user_id or (
            ticket_row.assigned_user_id if ticket_row else None
        )
        if assigned_user_id:
            assigned = self.db.scalar(select(User).where(
                User.id == assigned_user_id,
                User.active.is_(True),
                User.deleted_at.is_(None),
            ))
            recipients = [assigned] if assigned else []
        else:
            users = list(self.db.scalars(select(User).where(
                User.organization_id == conversation.organization_id,
                User.active.is_(True),
                User.deleted_at.is_(None),
            )).unique())
            recipients = [user for user in users
                          if user.can("customer_communications.read") or user.can("tickets.read")]

        target = f"/communications?status=unread#conversation-{conversation.id}"
        sender = conversation.contact.full_name if conversation.contact else communication.source_address
        subject = (
            f"Customer SMS Reply: [{ticket_row.ticket_number}] {sender}"
            if ticket_row else f"Customer SMS Reply: {conversation.customer.name}"
        )
        payload = {
            "conversation_id": conversation.id,
            "communication_id": communication.id,
            "ticket_id": ticket_id,
            "customer_id": conversation.customer_id,
        }
        for recipient in recipients:
            NotificationService(self.db).publish(
                "communications.customer_sms_reply",
                subject=subject,
                payload=payload,
                recipient_user_id=recipient.id,
                organization_id=recipient.organization_id,
                channel="internal",
                target_url=target,
            )
