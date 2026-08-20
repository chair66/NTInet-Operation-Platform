from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.communication_models import CommunicationProfile
from app.database.customer_communication_models import CustomerCommunication
from app.database.customer_models import Customer, CustomerContact
from app.database.ticket_models import Ticket, TicketOutboundMessage
from app.services.communication_profile_service import CommunicationProfileService
from app.services.bandwidth_messaging_client import BandwidthMessagingClient
from app.services.conversation_service import ConversationService
from app.services.ticket_communications import TicketCommunicationService, normalize_us_number
from app.services.email_signature_service import append_signature
from app.database.models import User


@dataclass(slots=True)
class CustomerCommunicationService:
    db: Session

    def list(self, customer_id: int, *, channel: str = "", limit: int = 100) -> list[CustomerCommunication]:
        statement = select(CustomerCommunication).where(CustomerCommunication.customer_id == customer_id)
        if channel in {"email", "sms"}:
            statement = statement.where(CustomerCommunication.channel == channel)
        return list(self.db.scalars(statement.order_by(CustomerCommunication.created_at.desc()).limit(max(1, min(limit, 500)))).unique())

    def send(self, customer: Customer, *, contact_id: int, channel: str, subject: str,
             body: str, profile_id: int | None, ticket_id: int | None,
             consent_override: bool, override_reason: str, actor_user_id: int,
             conversation_id: int | None = None,
             module_slug: str = "customer-management", html_body: str | None = None,
             email_attachments: list[tuple[str,bytes,str]] | None = None,
             estimate_id: int | None = None) -> CustomerCommunication:
        if channel not in {"email", "sms"} or not body.strip():
            raise ValueError("A valid channel and message are required.")
        if channel == "email" and not subject.strip():
            raise ValueError("An email subject is required.")
        contact = self.db.scalar(select(CustomerContact).where(
            CustomerContact.id == contact_id, CustomerContact.customer_id == customer.id,
            CustomerContact.active.is_(True)))
        if not contact:
            raise ValueError("The selected contact is not available for this customer.")
        if ticket_id and not self.db.scalar(select(Ticket.id).where(Ticket.id == ticket_id, Ticket.customer_id == customer.id)):
            raise ValueError("The selected ticket does not belong to this customer.")
        organization_id = customer.servicing_organization_id or customer.owner_organization_id
        profile_service = CommunicationProfileService(self.db)
        available = profile_service.available(organization_id, channel)
        profile = next((item for item in available if item.id == profile_id), None) if profile_id else profile_service.resolve_for_organization(organization_id, channel, module_slug)
        if profile_id and not profile:
            raise ValueError("The selected communication profile is not available to this customer.")
        destination = contact.email.strip().lower() if channel == "email" else normalize_us_number(contact.mobile_phone)
        error = ""
        if not profile:
            error = f"No active {channel.upper()} communication profile is available."
        elif not destination:
            error = f"The contact does not have a valid {channel.upper()} destination."
        elif channel == "sms" and contact.sms_consent_status != "consented":
            if not consent_override:
                error = f"SMS consent is {contact.sms_consent_status.replace('_', ' ')}."
            elif not override_reason.strip():
                raise ValueError("A reason is required when overriding SMS consent.")
        record = CustomerCommunication(
            customer_id=customer.id, contact_id=contact.id, ticket_id=ticket_id,
            estimate_id=estimate_id,
            organization_id=organization_id, communication_profile_id=profile.id if profile else None,
            direction="outbound", channel=channel, subject=subject.strip() if channel == "email" else "",
            body=body.strip(), source_address=profile.sender_address if profile else "",
            destination_address=destination, profile_name=profile.name if profile else "",
            provider=profile.provider if profile else ("smtp" if channel == "email" else "bandwidth"),
            status="suppressed" if error else "queued", error_message=error,
            consent_override=bool(channel == "sms" and consent_override),
            consent_override_reason=override_reason.strip() if channel == "sms" and consent_override else "",
            thread_key=f"customer-{customer.id}:{channel}:{contact.id}", created_by_user_id=actor_user_id,
        )
        self.db.add(record); self.db.flush()
        ConversationService(self.db).attach(record, conversation_id)
        return self.dispatch(record, html_body=html_body, email_attachments=email_attachments)

    def dispatch(self, record: CustomerCommunication, html_body: str | None = None, email_attachments: list[tuple[str,bytes,str]] | None = None) -> CustomerCommunication:
        settings = get_settings()
        if record.status == "suppressed":
            return record
        profile = record.communication_profile
        try:
            if not profile or not profile.is_active:
                raise RuntimeError("Communication profile is missing or inactive.")
            if profile.daily_limit:
                day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                customer_sent = self.db.scalar(select(func.count()).select_from(CustomerCommunication).where(
                    CustomerCommunication.communication_profile_id == profile.id,
                    CustomerCommunication.status.in_({"sent", "delivered"}),
                    CustomerCommunication.sent_at >= day_start)) or 0
                ticket_sent = self.db.scalar(select(func.count()).select_from(TicketOutboundMessage).where(
                    TicketOutboundMessage.communication_profile_id == profile.id,
                    TicketOutboundMessage.status.in_({"sent", "delivered"}),
                    TicketOutboundMessage.sent_at >= day_start)) or 0
                if int(customer_sent) + int(ticket_sent) >= profile.daily_limit:
                    raise RuntimeError("Communication profile daily sending limit reached.")
            if settings.ticket_communication_test_mode:
                record.status = "sent"; record.provider = "test-mode"
                record.provider_message_id = f"test-{uuid4().hex}"
                record.sent_at = datetime.now(timezone.utc); record.error_message = ""
                return record
            if record.channel == "email":
                if not settings.ticket_email_enabled:
                    record.status = "suppressed"; record.error_message = "Live email delivery is disabled."
                    return record
                html = html_body or ("<p>" + record.body.replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br>") + "</p>")
                html = append_signature(html,self.db.get(User,record.created_by_user_id))
                message_id = TicketCommunicationService._send_profile_email(
                    profile, record.subject or "Message from NTInet", html, record.destination_address, email_attachments)
                record.provider_message_id = message_id
                record.email_message_id = message_id
            else:
                if not settings.ticket_sms_enabled:
                    record.status = "suppressed"; record.error_message = "Live SMS delivery is disabled."
                    return record
                if not profile.credential_configured or not normalize_us_number(profile.sender_address):
                    raise RuntimeError("Bandwidth Messaging profile configuration is incomplete.")
                profile.sender_address = normalize_us_number(profile.sender_address)
                record.provider_message_id = BandwidthMessagingClient().send_sms(
                    profile, record.destination_address, record.body,
                    f"nop:customer:{record.customer_id}:{record.id}",
                )
            record.status = "sent"; record.sent_at = datetime.now(timezone.utc); record.error_message = ""
        except Exception as exc:
            record.status = "failed"; record.error_message = str(exc)[:2000]
        return record
