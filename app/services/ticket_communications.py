from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.ticket_models import Ticket, TicketEntry, TicketOutboundMessage
from app.services.notifications import render_email_template
from app.services.communication_profile_service import CommunicationProfileService
from app.services.bandwidth_messaging_client import BandwidthMessagingClient
from app.services.email_signature_service import append_signature


def normalize_us_number(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        digits = "1" + digits
    return f"+{digits}" if len(digits) == 11 and digits.startswith("1") else ""


@dataclass(slots=True)
class TicketCommunicationService:
    db: Session

    @staticmethod
    def ticket_destination(ticket: Ticket, channel: str) -> str:
        entry_type = "correspondence_email" if channel == "email" else "correspondence_mobile"
        entry = next((item for item in reversed(ticket.entries) if item.entry_type == entry_type), None)
        return entry.body.strip() if entry else ""

    def recipient(self, ticket: Ticket):
        return ticket.contact or ticket.customer.primary_contact

    def preferred_channels(self, ticket: Ticket) -> list[str]:
        ticket_channels = [
            channel for channel in ("email", "sms") if self.ticket_destination(ticket, channel)
        ]
        if ticket_channels:
            return ticket_channels
        contact = self.recipient(ticket)
        if contact and contact.preferred_channel == "sms" and contact.sms_consent_status == "consented":
            return ["sms"]
        return ["email"]

    def queue(
        self, ticket: Ticket, *, event_type: str, message: str,
        channels: list[str] | None = None, entry: TicketEntry | None = None,
        actor_user_id: int | None = None, dedupe_token: str = "", allow_sms_override: bool = False,
    ) -> list[TicketOutboundMessage]:
        contact = self.recipient(ticket)
        chosen = list(dict.fromkeys(channels or self.preferred_channels(ticket)))
        records: list[TicketOutboundMessage] = []
        for channel in chosen:
            if channel not in {"email", "sms"}:
                continue
            ticket_destination = self.ticket_destination(ticket, channel)
            destination = ticket_destination or (
                contact.email.strip().lower()
                if contact and channel == "email"
                else normalize_us_number(contact.mobile_phone if contact else "")
            )
            profile = CommunicationProfileService(self.db).resolve(ticket, channel)
            suppression = ""
            if not profile:
                suppression = f"No active {channel.upper()} communication profile is available."
            elif not contact and not ticket_destination:
                suppression = "No ticket contact or primary customer contact is available."
            elif not destination:
                suppression = f"No valid {channel.upper()} destination is available."
            elif channel == "sms" and not ticket_destination and contact.sms_consent_status != "consented" and not allow_sms_override:
                suppression = f"SMS consent is {contact.sms_consent_status.replace('_', ' ')}."
            token = dedupe_token or (f"entry-{entry.id}" if entry else uuid4().hex)
            key = f"ticket-{ticket.id}:{event_type}:{token}:{channel}"
            existing = self.db.scalar(select(TicketOutboundMessage).where(TicketOutboundMessage.deduplication_key == key))
            if existing:
                records.append(existing); continue
            subject = f"[{ticket.ticket_number}] {ticket.subject}"
            record = TicketOutboundMessage(
                ticket_id=ticket.id, entry_id=entry.id if entry else None,
                contact_id=contact.id if contact else None, channel=channel,
                communication_profile_id=profile.id if profile else None,
                profile_name=profile.name if profile else "", sender_identity=profile.sender_address if profile else "",
                destination=destination, subject=subject, body=message.strip(), event_type=event_type,
                status="suppressed" if suppression else "queued", provider=profile.provider if profile else ("smtp" if channel == "email" else "bandwidth"),
                deduplication_key=key, error_message=suppression, max_attempts=3,
                created_by_user_id=actor_user_id,
            )
            self.db.add(record); self.db.flush(); records.append(record)
        return records

    def queue_staff_email(
        self, ticket: Ticket, *, destination: str, event_type: str, message: str,
        dedupe_token: str, actor_user_id: int | None = None,
    ) -> TicketOutboundMessage:
        key = f"ticket-{ticket.id}:{event_type}:{dedupe_token}:email"
        existing = self.db.scalar(select(TicketOutboundMessage).where(TicketOutboundMessage.deduplication_key == key))
        if existing:
            return existing
        destination = destination.strip().lower()
        profile = CommunicationProfileService(self.db).resolve(ticket, "email")
        record = TicketOutboundMessage(
            ticket_id=ticket.id, channel="email", destination=destination,
            communication_profile_id=profile.id if profile else None,
            profile_name=profile.name if profile else "", sender_identity=profile.sender_address if profile else "",
            subject=f"[{ticket.ticket_number}] {ticket.subject}", body=message,
            event_type=event_type, status="queued" if destination and profile else "suppressed",
            provider=profile.provider if profile else "smtp", deduplication_key=key,
            error_message=("" if destination and profile else ("No active EMAIL communication profile is available." if destination else "Assigned user does not have an email address.")),
            created_by_user_id=actor_user_id,
        )
        self.db.add(record); self.db.flush(); return record

    def dispatch(self, record: TicketOutboundMessage) -> TicketOutboundMessage:
        settings = get_settings()
        if record.status in {"sent", "delivered", "suppressed"}:
            return record
        record.attempt_count += 1
        now = datetime.now(timezone.utc)
        try:
            profile = record.communication_profile
            if not profile or not profile.is_active: raise RuntimeError("Communication profile is missing or inactive.")
            if profile.daily_limit:
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                sent_today = self.db.scalar(select(func.count()).select_from(TicketOutboundMessage).where(
                    TicketOutboundMessage.communication_profile_id == profile.id,
                    TicketOutboundMessage.status.in_({"sent","delivered"}), TicketOutboundMessage.sent_at >= day_start)) or 0
                if int(sent_today) >= profile.daily_limit: raise RuntimeError("Communication profile daily sending limit reached.")
            if settings.ticket_communication_test_mode:
                record.status = "sent"; record.provider = "test-mode"
                record.provider_message_id = f"test-{uuid4().hex}"; record.sent_at = now
                record.error_message = ""; record.next_attempt_at = None
                return record
            if record.channel == "email":
                if not settings.ticket_email_enabled:
                    record.status = "suppressed"; record.error_message = "Live email delivery is disabled."
                    return record
                html = render_email_template(
                    "ticket_notification.html", ticket_number=record.ticket.ticket_number,
                    customer_name=record.ticket.customer.name, subject=record.subject,
                    message=record.body, ticket_url=f"{settings.ticket_public_base_url.rstrip('/')}/tickets/{record.ticket_id}",
                )
                html = append_signature(html,record.created_by or record.ticket.assigned_user)
                record.provider_message_id = self._send_profile_email(profile, record.subject, html, record.destination)
            else:
                if not settings.ticket_sms_enabled:
                    record.status = "suppressed"; record.error_message = "Live SMS delivery is disabled."
                    return record
                if not profile.credential_configured:
                    raise RuntimeError("Bandwidth Messaging credentials, application ID, and sending number are required.")
                sending_number = normalize_us_number(profile.sender_address)
                if not sending_number: raise RuntimeError("Bandwidth Messaging sending number must be a valid US number.")
                sms = render_email_template(
                    "ticket_sms.txt", ticket_number=record.ticket.ticket_number,
                    message=record.body, ticket_url=f"{settings.ticket_public_base_url.rstrip('/')}/tickets/{record.ticket_id}",
                )
                profile.sender_address = sending_number
                record.provider_message_id = BandwidthMessagingClient().send_sms(
                    profile, record.destination, sms, f"nop:{record.ticket.ticket_number}:{record.id}"
                )
            record.status = "sent"; record.sent_at = now; record.error_message = ""; record.next_attempt_at = None
        except Exception as exc:
            record.status = "failed"; record.failed_at = now; record.error_message = str(exc)[:2000]
            record.next_attempt_at = now + timedelta(minutes=5 * (2 ** max(record.attempt_count - 1, 0))) if record.attempt_count < record.max_attempts else None
        return record

    @staticmethod
    def _send_profile_email(profile, subject: str, html: str, destination: str, attachments: list[tuple[str,bytes,str]] | None = None) -> str:
        message = EmailMessage(); message["Subject"] = subject
        message["From"] = f"{profile.from_name} <{profile.sender_address}>" if profile.from_name else profile.sender_address
        message["To"] = destination
        message["Message-ID"] = make_msgid(domain=(profile.sender_address.split("@", 1)[1] if "@" in profile.sender_address else None))
        if profile.reply_to: message["Reply-To"] = profile.reply_to
        message.set_content(re.sub(r"<[^>]+>", " ", html)); message.add_alternative(html, subtype="html")
        for filename,data,content_type in attachments or []:
            main,sub=(content_type.split("/",1)+["octet-stream"])[:2] if "/" in content_type else ("application","octet-stream")
            message.add_attachment(data,maintype=main,subtype=sub,filename=filename)
        context = ssl.create_default_context()
        if profile.smtp_security == "ssl":
            server = smtplib.SMTP_SSL(profile.smtp_host, profile.smtp_port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(profile.smtp_host, profile.smtp_port, timeout=20)
            if profile.smtp_security == "starttls": server.starttls(context=context)
        try:
            if profile.smtp_username:
                server.login(profile.smtp_username, CommunicationProfileService.password(profile))
            refused = server.send_message(message)
            if refused:
                details = ", ".join(f"{address}: {reason}" for address, reason in refused.items())
                raise RuntimeError(f"SMTP server refused one or more recipients: {details}")
        finally:
            server.quit()
        # SMTP has accepted the message for delivery at this point. This is not
        # proof that the destination mailbox ultimately received it.
        return str(message["Message-ID"])

    def dispatch_all(self, records: list[TicketOutboundMessage]) -> None:
        for record in records:
            self.dispatch(record)

    def retry(self, record: TicketOutboundMessage) -> TicketOutboundMessage:
        if record.status not in {"failed", "queued"}:
            raise ValueError("Only queued or failed messages can be retried.")
        if record.attempt_count >= record.max_attempts:
            record.attempt_count = 0
        record.status = "queued"; record.error_message = ""; record.next_attempt_at = None
        return self.dispatch(record)

    def process_due(self, limit: int = 100) -> list[TicketOutboundMessage]:
        now = datetime.now(timezone.utc)
        records = list(self.db.scalars(
            select(TicketOutboundMessage).where(
                TicketOutboundMessage.status.in_({"queued", "failed"}),
                TicketOutboundMessage.attempt_count < TicketOutboundMessage.max_attempts,
                or_(TicketOutboundMessage.next_attempt_at.is_(None), TicketOutboundMessage.next_attempt_at <= now),
            ).order_by(TicketOutboundMessage.created_at).limit(max(1, min(limit, 500)))
        ).unique())
        overdue = list(self.db.scalars(
            select(Ticket).where(
                Ticket.status.not_in({"resolved", "closed"}),
                Ticket.sla_target_at.is_not(None), Ticket.sla_target_at <= now,
                Ticket.assigned_user_id.is_not(None),
            ).limit(max(1, min(limit, 500)))
        ).unique())
        for ticket in overdue:
            if ticket.assigned_user:
                token = ticket.sla_target_at.isoformat() if ticket.sla_target_at else str(ticket.id)
                records.append(self.queue_staff_email(
                    ticket, destination=ticket.assigned_user.email, event_type="sla_breached",
                    message=f"SLA target has passed for {ticket.ticket_number}. Current status: {ticket.status.replace('_', ' ').title()}.",
                    dedupe_token=token,
                ))
        self.dispatch_all(records)
        return records
