from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
import hashlib
import hmac
import json
import logging
from pathlib import Path
import secrets
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.database.customer_models import CustomerContact
from app.database.models import NotificationEvent
from app.database.ticket_models import Ticket, TicketAttachment, TicketEntry, TicketOutboundMessage
from app.security import context_from_request, require_permission
from app.services import AuditService, TicketService
from app.services.ticket_service import TICKET_PRIORITIES, TICKET_STATUSES, TICKET_TYPES
from app.services.ticket_communications import TicketCommunicationService, normalize_us_number
from app.services.communication_profile_service import CommunicationProfileService
from app.services.bandwidth_messaging_client import BandwidthMessagingClient
from app.web import render


router = APIRouter(prefix="/tickets", tags=["Support Tickets"])
settings = get_settings()
logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "new": "New", "open": "Open", "pending_customer": "Pending Customer",
    "scheduled": "Scheduled", "resolved": "Resolved", "closed": "Closed",
}
PRIORITY_LABELS = {"low": "Low", "normal": "Normal", "high": "High", "urgent": "Urgent"}
TYPE_LABELS = {
    "no_internet_all_devices": "Internet — No Internet, All Devices",
    "no_internet_single_device": "Internet — No Internet, Single Device",
    "internet_slow": "Internet — Slow Speeds", "internet_intermittent": "Internet — Intermittent",
    "internet_wifi": "Internet — Wi-Fi Issue", "internet_other": "Internet — Other",
    "phone_no_dial_tone": "Phone — No Dial Tone", "phone_inbound": "Phone — Cannot Receive Calls",
    "phone_outbound": "Phone — Cannot Make Calls", "phone_quality": "Phone — Call Quality",
    "phone_voicemail": "Phone — Voicemail", "phone_other": "Phone — Other",
    "email_send_receive": "Email — Cannot Send or Receive", "email_login": "Email — Login or Password",
    "email_spam": "Email — Spam or Filtering", "email_setup": "Email — Device Setup",
    "email_other": "Email — Other", "billing_question": "Billing — Account Question",
    "billing_payment": "Billing — Payment", "billing_charge": "Billing — Charge or Invoice",
    "billing_other": "Billing — Other", "service_request": "Other — Service Request", "other": "Other",
    "phone": "Phone (Legacy)", "support": "Support (Legacy)", "outage": "Outage (Legacy)",
    "installation": "Installation (Legacy)", "billing": "Billing (Legacy)",
}
AFFECTED_SERVICE_ISSUES = {
    "internet": [
        ("no_internet_all_devices", "No Internet — All Devices"),
        ("no_internet_single_device", "No Internet — Single Device"),
        ("internet_slow", "Slow Speeds"), ("internet_intermittent", "Intermittent Connection"),
        ("internet_wifi", "Wi-Fi Issue"), ("internet_other", "Other Internet Issue"),
    ],
    "phone": [
        ("phone_no_dial_tone", "No Dial Tone"), ("phone_inbound", "Cannot Receive Calls"),
        ("phone_outbound", "Cannot Make Calls"), ("phone_quality", "Call Quality"),
        ("phone_voicemail", "Voicemail"), ("phone_other", "Other Phone Issue"),
    ],
    "email": [
        ("email_send_receive", "Cannot Send or Receive"), ("email_login", "Login or Password"),
        ("email_spam", "Spam or Filtering"), ("email_setup", "Device Setup"),
        ("email_other", "Other Email Issue"),
    ],
    "billing": [
        ("billing_question", "Account Question"), ("billing_payment", "Payment"),
        ("billing_charge", "Charge or Invoice"), ("billing_other", "Other Billing Issue"),
    ],
    "other": [("service_request", "Service Request"), ("other", "Other")],
}
ALLOWED_ATTACHMENT_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".log", ".csv",
    ".doc", ".docx", ".xls", ".xlsx",
}


def parse_datetime(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date/time value") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_optional_int(value: str | int | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid selection") from exc


def ticket_or_404(service: TicketService, ticket_id: int) -> Ticket:
    ticket = service.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def redirect_to_ticket(ticket_id: int, message: str = "") -> RedirectResponse:
    suffix = f"?message={quote(message)}" if message else ""
    return RedirectResponse(f"/tickets/{ticket_id}{suffix}", status_code=303)


def valid_email_address(value: str) -> str:
    address = parseaddr((value or "").strip())[1].lower()
    if not address or "@" not in address or "." not in address.rsplit("@", 1)[-1]:
        return ""
    return address


def send_contact_verification(
    db, organization_id: int, destination: str, confirmation_url: str, tag: str,
) -> None:
    profile = CommunicationProfileService(db).resolve_for_organization(
        organization_id, "sms", "support-tickets"
    )
    if not profile:
        raise ValueError("No active SMS communication profile is available for this customer.")
    if not profile.credential_configured:
        raise ValueError("The selected SMS communication profile is not fully configured.")
    if not settings.ticket_sms_enabled:
        raise ValueError("Live SMS delivery is disabled.")
    sending_number = normalize_us_number(profile.sender_address)
    if not sending_number:
        raise ValueError("The Bandwidth sending number is invalid.")
    profile.sender_address = sending_number
    BandwidthMessagingClient().send_sms(
        profile,
        destination,
        f"NTInet Support would like to use this mobile number for a support ticket. Confirm receipt: {confirmation_url} This link expires in 30 minutes.",
        tag,
    )


def send_email_verification(db, organization_id: int, destination: str,
                            confirmation_url: str) -> None:
    profile = CommunicationProfileService(db).resolve_for_organization(
        organization_id, "email", "support-tickets"
    )
    if not profile:
        raise ValueError("No active EMAIL communication profile is available for this customer.")
    if not profile.credential_configured:
        raise ValueError("The selected EMAIL communication profile is not fully configured.")
    if not settings.ticket_email_enabled:
        raise ValueError("Live email delivery is disabled.")
    html = (
        "<p>NTInet Support would like to use this email address for a support ticket.</p>"
        "<p>Click the button below to confirm that you received this message and approve this address for ticket correspondence.</p>"
        f"<p><a href=\"{confirmation_url}\" style=\"display:inline-block;padding:12px 20px;background:#dc0017;color:#fff;text-decoration:none;border-radius:4px;font-weight:700\">Confirm Email Address</a></p>"
        "<p>This confirmation link expires in 30 minutes. If you did not request support, ignore this message.</p>"
    )
    TicketCommunicationService._send_profile_email(
        profile, "Confirm your email for NTInet Support", html, destination
    )


def verify_new_ticket_destination(request: Request, db, customer_id: int, channel: str,
                                  destination: str, proof: str) -> tuple[str, NotificationEvent | None]:
    if not destination.strip():
        return "", None
    normalized = valid_email_address(destination) if channel == "email" else normalize_us_number(destination)
    if not normalized:
        raise ValueError(f"Enter a valid {'email address' if channel == 'email' else '10-digit US mobile number'}.")
    try:
        event_id = int(proof)
    except (TypeError, ValueError) as exc:
        label = "email" if channel == "email" else "mobile number"
        raise ValueError(f"Send the verification message and have the recipient confirm the {label} before creating the ticket.") from exc
    expected_type = "tickets.email_verification" if channel == "email" else "tickets.mobile_verification"
    event = db.get(NotificationEvent, event_id)
    if not event or event.event_type != expected_type or event.actor_user_id != context_from_request(request).user_id:
        raise ValueError(f"The {channel} verification request is not valid for this ticket.")
    try:
        payload = json.loads(event.payload or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"The {channel} verification request could not be read.") from exc
    if int(payload.get("customer_id", 0)) != customer_id or payload.get("destination") != normalized:
        raise ValueError(f"The confirmed {channel} destination does not match this customer and address or number.")
    if datetime.now(timezone.utc) > event.created_at + timedelta(minutes=30):
        event.status = "expired"
        raise ValueError(f"The {channel} confirmation expired. Send a new verification message.")
    if event.status != "confirmed":
        raise ValueError(f"The recipient has not confirmed receipt of the {channel} verification message yet.")
    return normalized, event


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def ticket_list(
    request: Request, q: str = "", status: str = "", priority: str = "",
    ticket_type: str = "", assigned_user_id: str = "",
    customer_id: str = "",
):
    require_permission(request, "tickets.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context)
        assigned_id = parse_optional_int(assigned_user_id)
        selected_customer_id = parse_optional_int(customer_id)
        tickets = service.list(
            query=q, status=status, priority=priority, ticket_type=ticket_type,
            assigned_user_id=assigned_id, customer_id=selected_customer_id,
        )
        visible = service.scope(select(Ticket))
        total = int(db.scalar(select(func.count()).select_from(visible.subquery())) or 0)
        open_count = sum(1 for item in service.list(limit=2000) if item.status not in {"resolved", "closed"})
        urgent_count = sum(1 for item in service.list(priority="urgent", limit=2000) if item.status != "closed")
        users = service.assignable_users()
        customers = service.visible_customers()
        db.expunge_all()
    return render(
        request, "tickets/list.html", tickets=tickets, users=users, customers=customers,
        metrics={"total": total, "open": open_count, "urgent": urgent_count},
        filters={"q": q, "status": status, "priority": priority, "ticket_type": ticket_type,
                 "assigned_user_id": assigned_id, "customer_id": selected_customer_id},
        status_labels=STATUS_LABELS, priority_labels=PRIORITY_LABELS, type_labels=TYPE_LABELS,
    )


def render_new_ticket_form(
    request: Request, *, customer_id: int | None = None, error: str = "",
    form_data: dict | None = None, status_code: int = 200,
):
    """Render the new-ticket form with NOP styling, optionally preserving submitted values."""
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context)
        customers = service.visible_customers()
        users = service.assignable_users()
        selected = next((item for item in customers if item.id == customer_id), None)
        for customer in customers:
            _ = tuple(customer.contacts); _ = tuple(customer.locations)
        db.expunge_all()
    return render(
        request, "tickets/form.html", ticket=None, customers=customers, users=users,
        selected_customer=selected, status_labels=STATUS_LABELS,
        priority_labels=PRIORITY_LABELS, type_labels=TYPE_LABELS,
        affected_service_issues=AFFECTED_SERVICE_ISSUES, error=error,
        form_data=form_data or {}, status_code=status_code,
    )


@router.get("/new", response_class=HTMLResponse)
def ticket_new(request: Request, customer_id: int | None = None):
    require_permission(request, "tickets.create")
    return render_new_ticket_form(request, customer_id=customer_id)


@router.post("/contact-verification/send")
def new_ticket_contact_verification_send(
    request: Request, customer_id: int = Form(...), channel: str = Form(...),
    destination: str = Form(...),
):
    require_permission(request, "tickets.create")
    if channel not in {"email", "mobile"}:
        raise HTTPException(status_code=400, detail="Choose email or mobile verification.")
    context = context_from_request(request)
    with SessionLocal() as db:
        customer = TicketService(db, context).visible_customers()
        customer = next((item for item in customer if item.id == customer_id), None)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found or unavailable.")
        normalized = valid_email_address(destination) if channel == "email" else normalize_us_number(destination)
        if not normalized:
            raise HTTPException(
                status_code=400,
                detail=f"Enter a valid {'email address' if channel == 'email' else '10-digit US mobile number'}.",
            )
        if channel == "email":
            recent_cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)
            recent = db.scalar(select(NotificationEvent).where(
                NotificationEvent.event_type == "tickets.email_verification",
                NotificationEvent.actor_user_id == context.user_id,
                NotificationEvent.created_at >= recent_cutoff,
            ).order_by(NotificationEvent.created_at.desc()))
            if recent:
                raise HTTPException(status_code=429, detail="Please wait 60 seconds before sending another verification email.")
            token = secrets.token_urlsafe(32)
            event = NotificationEvent(
                organization_id=customer.owner_organization_id,
                actor_user_id=context.user_id,
                event_type="tickets.email_verification", channel="email",
                subject=f"Verify {normalized}", status="sending",
                payload=json.dumps({
                    "customer_id": customer.id, "destination": normalized,
                    "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                }, sort_keys=True),
            )
            db.add(event); db.flush()
            confirmation_url = (
                f"{settings.ticket_public_base_url.rstrip('/')}/tickets/contact-verification/"
                f"email/confirm/{event.id}/{token}"
            )
            try:
                send_email_verification(db, customer.owner_organization_id, normalized, confirmation_url)
            except Exception as exc:
                event.status = "failed"; db.commit()
                raise HTTPException(status_code=502, detail=f"Unable to send verification email: {exc}") from exc
            event.status = "sent"; db.commit()
            return {"ok": True, "destination": normalized, "verification_id": event.id,
                    "message": f"Verification email sent to {normalized}. Waiting for the recipient to confirm receipt."}
        recent_cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)
        recent = db.scalar(select(NotificationEvent).where(
            NotificationEvent.event_type == "tickets.mobile_verification",
            NotificationEvent.actor_user_id == context.user_id,
            NotificationEvent.created_at >= recent_cutoff,
        ).order_by(NotificationEvent.created_at.desc()))
        if recent:
            raise HTTPException(status_code=429, detail="Please wait 60 seconds before sending another verification text.")
        token = secrets.token_urlsafe(32)
        event = NotificationEvent(
            organization_id=customer.owner_organization_id,
            actor_user_id=context.user_id,
            event_type="tickets.mobile_verification", channel="sms",
            subject=f"Verify {normalized}", status="sending",
            payload=json.dumps({
                "customer_id": customer.id, "destination": normalized,
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
            }, sort_keys=True),
        )
        db.add(event); db.flush()
        confirmation_url = (
            f"{settings.ticket_public_base_url.rstrip('/')}/tickets/contact-verification/"
            f"mobile/confirm/{event.id}/{token}"
        )
        try:
            send_contact_verification(
                db, customer.owner_organization_id, normalized, confirmation_url,
                f"nop:new-ticket-verification:{customer.id}:{channel}",
            )
        except Exception as exc:
            event.status = "failed"; db.commit()
            raise HTTPException(status_code=502, detail=f"Unable to send verification text: {exc}") from exc
        event.status = "sent"; db.commit()
        return {"ok": True, "destination": normalized, "verification_id": event.id,
                "message": f"Verification text sent to {normalized}. Waiting for the recipient to confirm receipt."}


@router.get("/contact-verification/email/confirm/{event_id}/{token}", response_class=HTMLResponse)
def confirm_new_ticket_email(request: Request, event_id: int, token: str):
    error = ""; destination = ""
    with SessionLocal() as db:
        event = db.get(NotificationEvent, event_id)
        if not event or event.event_type != "tickets.email_verification":
            error = "This email confirmation link is invalid."
        else:
            try:
                payload = json.loads(event.payload or "{}")
            except json.JSONDecodeError:
                payload = {}
            destination = str(payload.get("destination", ""))
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if not hmac.compare_digest(token_hash, str(payload.get("token_hash", ""))):
                error = "This email confirmation link is invalid."
            elif datetime.now(timezone.utc) > event.created_at + timedelta(minutes=30):
                event.status = "expired"; db.commit()
                error = "This email confirmation link has expired. Ask NTInet Support to send another email."
            elif event.status == "consumed":
                error = "This email address was already confirmed and used for a support ticket."
            else:
                event.status = "confirmed"; event.processed_at = datetime.now(timezone.utc)
                db.commit()
    return render(request, "tickets/email_verified.html", public_page=True,
                  destination=destination, error=error, status_code=400 if error else 200)


@router.get("/contact-verification/mobile/confirm/{event_id}/{token}", response_class=HTMLResponse)
def confirm_new_ticket_mobile(request: Request, event_id: int, token: str):
    error = ""; destination = ""
    with SessionLocal() as db:
        event = db.get(NotificationEvent, event_id)
        if not event or event.event_type != "tickets.mobile_verification":
            error = "This mobile confirmation link is invalid."
        else:
            try:
                payload = json.loads(event.payload or "{}")
            except json.JSONDecodeError:
                payload = {}
            destination = str(payload.get("destination", ""))
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if not hmac.compare_digest(token_hash, str(payload.get("token_hash", ""))):
                error = "This mobile confirmation link is invalid."
            elif datetime.now(timezone.utc) > event.created_at + timedelta(minutes=30):
                event.status = "expired"; db.commit()
                error = "This mobile confirmation link has expired. Ask NTInet Support to send another text."
            elif event.status == "consumed":
                error = "This mobile number was already confirmed and used for a support ticket."
            else:
                event.status = "confirmed"; event.processed_at = datetime.now(timezone.utc)
                db.commit()
    return render(request, "tickets/mobile_verified.html", public_page=True,
                  destination=destination, error=error, status_code=400 if error else 200)


@router.post("/contact-verification/email/status")
def new_ticket_email_verification_status(
    request: Request, verification_id: str = Form(""), customer_id: str = Form(""),
    destination: str = Form(""),
):
    require_permission(request, "tickets.create")
    context = context_from_request(request)
    normalized = valid_email_address(destination)
    try:
        resolved_customer_id = int(customer_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Select a customer before checking verification.") from exc
    if not normalized:
        raise HTTPException(status_code=400, detail="Enter a valid email address before checking verification.")
    with SessionLocal() as db:
        event = db.get(NotificationEvent, int(verification_id)) if verification_id.isdigit() else None
        if event is None:
            candidates = db.scalars(select(NotificationEvent).where(
                NotificationEvent.event_type == "tickets.email_verification",
                NotificationEvent.actor_user_id == context.user_id,
            ).order_by(NotificationEvent.created_at.desc()).limit(20))
            for candidate in candidates:
                try: candidate_payload = json.loads(candidate.payload or "{}")
                except json.JSONDecodeError: continue
                if int(candidate_payload.get("customer_id", 0)) == resolved_customer_id and candidate_payload.get("destination") == normalized:
                    event = candidate; break
        if not event or event.event_type != "tickets.email_verification" or event.actor_user_id != context.user_id:
            raise HTTPException(status_code=404, detail="Verification request not found.")
        try: payload = json.loads(event.payload or "{}")
        except json.JSONDecodeError as exc: raise HTTPException(status_code=400, detail="Verification request is invalid.") from exc
        if int(payload.get("customer_id", 0)) != resolved_customer_id or payload.get("destination") != normalized:
            raise HTTPException(status_code=400, detail="The verification request no longer matches this ticket.")
        expired = datetime.now(timezone.utc) > event.created_at + timedelta(minutes=30)
        if expired and event.status not in {"confirmed", "consumed"}:
            event.status = "expired"; db.commit()
        return {"confirmed": event.status in {"confirmed", "consumed"}, "status": event.status,
                "destination": normalized, "verification_id": event.id}


@router.post("/contact-verification/mobile/status")
def new_ticket_mobile_verification_status(
    request: Request, verification_id: str = Form(""), customer_id: str = Form(""),
    destination: str = Form(""),
):
    require_permission(request, "tickets.create")
    context = context_from_request(request)
    normalized = normalize_us_number(destination)
    try:
        resolved_customer_id = int(customer_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Select a customer before checking verification.") from exc
    if not normalized:
        raise HTTPException(status_code=400, detail="Enter a valid mobile number before checking verification.")
    with SessionLocal() as db:
        event = db.get(NotificationEvent, int(verification_id)) if verification_id.isdigit() else None
        if event is None:
            candidates = db.scalars(select(NotificationEvent).where(
                NotificationEvent.event_type == "tickets.mobile_verification",
                NotificationEvent.actor_user_id == context.user_id,
            ).order_by(NotificationEvent.created_at.desc()).limit(20))
            for candidate in candidates:
                try: candidate_payload = json.loads(candidate.payload or "{}")
                except json.JSONDecodeError: continue
                if int(candidate_payload.get("customer_id", 0)) == resolved_customer_id and candidate_payload.get("destination") == normalized:
                    event = candidate; break
        if not event or event.event_type != "tickets.mobile_verification" or event.actor_user_id != context.user_id:
            raise HTTPException(status_code=404, detail="Verification request not found.")
        try: payload = json.loads(event.payload or "{}")
        except json.JSONDecodeError as exc: raise HTTPException(status_code=400, detail="Verification request is invalid.") from exc
        if int(payload.get("customer_id", 0)) != resolved_customer_id or payload.get("destination") != normalized:
            raise HTTPException(status_code=400, detail="The verification request no longer matches this ticket.")
        expired = datetime.now(timezone.utc) > event.created_at + timedelta(minutes=30)
        if expired and event.status not in {"confirmed", "consumed"}:
            event.status = "expired"; db.commit()
        return {"confirmed": event.status in {"confirmed", "consumed"}, "status": event.status,
                "destination": normalized, "verification_id": event.id}


@router.post("")
def ticket_create(
    request: Request, customer_id: int = Form(...), subject: str = Form(...),
    description: str = Form(...), contact_id: str = Form(""),
    location_id: str = Form(""), callback_number: str = Form(""),
    affected_service: str = Form(...), ticket_type: str = Form(...), priority: str = Form("normal"),
    assigned_user_id: str = Form(""), correspondence_mode: str = Form("account"),
    correspondence_email: str = Form(""), correspondence_email_code: str = Form(""),
    correspondence_mobile: str = Form(""), correspondence_mobile_code: str = Form(""),
    save_to_account_contact: str | None = Form(None),
):
    require_permission(request, "tickets.create")
    context = context_from_request(request)
    ticket_id: int | None = None

    # Phase 1 is the hard success boundary: validate and persist the actual ticket
    # and any explicitly verified contact changes.  Email/SMS delivery and audit
    # logging must never be able to roll the ticket back or turn a successful
    # submit into a browser 500.
    with SessionLocal() as db:
        service = TicketService(db, context)
        try:
            if correspondence_mode not in {"account", "additional"}:
                raise ValueError("Choose a valid correspondence option.")
            verified_email = verified_mobile = ""
            email_verification_event = None
            mobile_verification_event = None
            update_account_contact = bool(save_to_account_contact)
            selected_contact_id = parse_optional_int(contact_id)
            if update_account_contact and not context.can("customers.manage"):
                raise ValueError("You do not have permission to update customer contacts.")
            if update_account_contact and not selected_contact_id:
                raise ValueError("Select an account contact before saving verified information to the account.")
            if update_account_contact and correspondence_mode != "additional":
                raise ValueError("Choose additional correspondence before updating the account contact.")
            if correspondence_mode == "additional":
                if not correspondence_email.strip() and not correspondence_mobile.strip():
                    raise ValueError("Enter and verify an additional email address or mobile number.")
                verified_email, email_verification_event = verify_new_ticket_destination(
                    request, db, customer_id, "email", correspondence_email, correspondence_email_code
                )
                verified_mobile, mobile_verification_event = verify_new_ticket_destination(
                    request, db, customer_id, "mobile", correspondence_mobile, correspondence_mobile_code
                )
            normalized_callback = normalize_us_number(callback_number) if callback_number.strip() else ""
            if callback_number.strip() and not normalized_callback:
                raise ValueError("Callback number must be a valid 10-digit US telephone number.")
            valid_issues = {value for value, _label in AFFECTED_SERVICE_ISSUES.get(affected_service, [])}
            if ticket_type not in valid_issues:
                raise ValueError("Select a valid issue for the affected service.")

            ticket = service.create(
                customer_id=customer_id, subject=subject, description=description,
                contact_id=selected_contact_id, location_id=parse_optional_int(location_id),
                service_id=None, ticket_type=ticket_type,
                priority=priority, assigned_user_id=parse_optional_int(assigned_user_id),
                due_at=None, callback_number=normalized_callback,
            )
            if verified_email:
                ticket.entries.append(TicketEntry(
                    entry_type="correspondence_email", visibility="internal", body=verified_email,
                    author_user_id=context.user_id,
                ))
            if verified_mobile:
                ticket.entries.append(TicketEntry(
                    entry_type="correspondence_mobile", visibility="internal", body=verified_mobile,
                    author_user_id=context.user_id,
                ))

            if update_account_contact:
                account_contact = db.get(CustomerContact, selected_contact_id)
                if account_contact is None or account_contact.customer_id != ticket.customer_id:
                    raise ValueError("The selected contact is not available for this customer.")
                updated_fields = []
                if verified_email:
                    account_contact.email = verified_email
                    updated_fields.append("email address")
                if verified_mobile:
                    account_contact.mobile_phone = verified_mobile
                    updated_fields.append("mobile number")
                ticket.entries.append(TicketEntry(
                    entry_type="account_contact_update", visibility="internal",
                    body=f"Verified and updated {' and '.join(updated_fields)} on account contact {account_contact.full_name}.",
                    author_user_id=context.user_id,
                ))

            db.flush()
            if email_verification_event is not None:
                email_verification_event.status = "consumed"
                email_verification_event.target_url = f"/tickets/{ticket.id}"
            if mobile_verification_event is not None:
                mobile_verification_event.status = "consumed"
                mobile_verification_event.target_url = f"/tickets/{ticket.id}"
            ticket_id = ticket.id
            db.commit()
        except ValueError as exc:
            db.rollback()
            return render_new_ticket_form(
                request, customer_id=customer_id, error=str(exc), status_code=400,
                form_data={
                    "customer_id": customer_id, "subject": subject, "description": description,
                    "contact_id": contact_id, "location_id": location_id,
                    "callback_number": callback_number, "affected_service": affected_service,
                    "ticket_type": ticket_type, "priority": priority,
                    "assigned_user_id": assigned_user_id,
                    "correspondence_mode": correspondence_mode,
                    "correspondence_email": correspondence_email,
                    "correspondence_email_code": correspondence_email_code,
                    "correspondence_mobile": correspondence_mobile,
                    "correspondence_mobile_code": correspondence_mobile_code,
                    "save_to_account_contact": bool(save_to_account_contact),
                },
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.exception("Ticket persistence failed for customer_id=%s", customer_id)
            raise HTTPException(
                status_code=500,
                detail=f"Ticket could not be saved. No duplicate ticket was created. Error: {exc}",
            ) from exc

    # Phase 2 is best-effort post-processing.  A provider, SMTP, SMS, template,
    # or audit failure is logged but does not invalidate the ticket that was
    # already committed above.
    try:
        with SessionLocal() as db:
            service = TicketService(db, context)
            ticket = ticket_or_404(service, int(ticket_id))
            verified_email = TicketCommunicationService.ticket_destination(ticket, "email")
            verified_mobile = TicketCommunicationService.ticket_destination(ticket, "sms")
            communications = TicketCommunicationService(db)
            messages = communications.queue(
                ticket, event_type="ticket_created",
                message=f"Your support request has been received. We will provide updates on {ticket.ticket_number}.",
                channels=([channel for channel, value in (("email", verified_email), ("sms", verified_mobile)) if value] or None),
                actor_user_id=context.user_id, dedupe_token="created",
            ) if settings.ticket_auto_new_confirmation else []
            communications.dispatch_all(messages)
            for outbound in messages:
                AuditService(db, request, context).record(
                    "tickets.automatic_message", "ticket", ticket.id,
                    f"Automatic {outbound.channel.upper()} {outbound.status}: ticket created",
                    module="support-tickets", organization_id=ticket.owning_organization_id,
                    event_data={"outbound_message_id": outbound.id},
                )

            # A newly-created ticket also needs an internal notification for the
            # technician it is assigned to. Previously technicians were only
            # emailed when an existing ticket's assignment changed.
            if ticket.assigned_user and (ticket.assigned_user.email or "").strip():
                tech_message = communications.queue_staff_email(
                    ticket, destination=ticket.assigned_user.email, event_type="ticket_assigned",
                    message=(
                        f"{ticket.ticket_number} has been assigned to you. "
                        f"Priority: {ticket.priority.title()}. Customer: {ticket.customer.name}."
                    ),
                    dedupe_token=f"created-assignment-{ticket.assigned_user.id}",
                    actor_user_id=context.user_id,
                )
                communications.dispatch(tech_message)
                AuditService(db, request, context).record(
                    "tickets.assignment_message", "ticket", ticket.id,
                    f"Assignment EMAIL {tech_message.status} to {ticket.assigned_user.email}",
                    module="support-tickets", organization_id=ticket.owning_organization_id,
                    event_data={"outbound_message_id": tech_message.id},
                )

            AuditService(db, request, context).record(
                "tickets.created", "ticket", ticket.id,
                f"Created {ticket.ticket_number}: {ticket.subject}", module="support-tickets",
                organization_id=ticket.owning_organization_id,
            )
            db.commit()
    except Exception:
        logger.exception("Ticket %s was created, but post-submit processing failed", ticket_id)

    return redirect_to_ticket(int(ticket_id), "Ticket created.")


@router.get("/communications", response_class=HTMLResponse)
def ticket_communication_settings(request: Request):
    require_permission(request, "tickets.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        profiles = CommunicationProfileService(db, context).manageable()
        email_profiles = [item for item in profiles if item.channel == "email"]
        sms_profiles = [item for item in profiles if item.channel == "sms"]
        smtp_ready = any(item.is_active and item.credential_configured for item in email_profiles)
        sms_ready = any(item.is_active and item.credential_configured for item in sms_profiles)
    return render(
        request, "tickets/communications.html", smtp_ready=smtp_ready, sms_ready=sms_ready,
        email_profile_count=len(email_profiles), sms_profile_count=len(sms_profiles),
        communication_test_mode=settings.ticket_communication_test_mode,
        ticket_email_enabled=settings.ticket_email_enabled, ticket_sms_enabled=settings.ticket_sms_enabled,
        auto_new=settings.ticket_auto_new_confirmation,
        auto_status=settings.ticket_auto_status_notifications,
    )


@router.get("/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(request: Request, ticket_id: int, message: str = "", error: str = ""):
    require_permission(request, "tickets.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context)
        ticket = ticket_or_404(service, ticket_id)
        users = service.assignable_users()
        profile_service = CommunicationProfileService(db, context)
        email_profiles = profile_service.available(ticket.owning_organization_id, "email")
        sms_profiles = profile_service.available(ticket.owning_organization_id, "sms")
        _ = tuple(ticket.entries); _ = tuple(ticket.attachments)
        _ = tuple(ticket.outbound_messages)
        _ = tuple(ticket.jobs)
        db.expunge_all()
        callback_entry = next((entry for entry in reversed(ticket.entries) if entry.entry_type == "callback_number"), None)
        correspondence_email_entry = next((entry for entry in reversed(ticket.entries) if entry.entry_type == "correspondence_email"), None)
        correspondence_mobile_entry = next((entry for entry in reversed(ticket.entries) if entry.entry_type == "correspondence_mobile"), None)
        account_contact_update_entry = next((entry for entry in reversed(ticket.entries) if entry.entry_type == "account_contact_update"), None)
    return render(
        request, "tickets/detail.html", ticket=ticket, users=users, message=message, error=error,
        email_profiles=email_profiles, sms_profiles=sms_profiles,
        status_labels=STATUS_LABELS, priority_labels=PRIORITY_LABELS, type_labels=TYPE_LABELS,
        communication_test_mode=settings.ticket_communication_test_mode,
        ticket_email_enabled=settings.ticket_email_enabled,
        ticket_sms_enabled=settings.ticket_sms_enabled,
        callback_number=callback_entry.body if callback_entry else "",
        ticket_contact=ticket.contact or ticket.customer.primary_contact,
        correspondence_email=correspondence_email_entry.body if correspondence_email_entry else "",
        correspondence_mobile=correspondence_mobile_entry.body if correspondence_mobile_entry else "",
        account_contact_updated=bool(account_contact_update_entry),
    )


@router.post("/{ticket_id}/update")
def ticket_update(
    request: Request, ticket_id: int, status: str = Form(...), priority: str = Form(...),
    ticket_type: str = Form(...), assigned_user_id: str = Form(""),
    due_at: str = Form(""), subject: str = Form(...),
    email_profile_id: str = Form(""), sms_profile_id: str = Form(""),
):
    require_permission(request, "tickets.manage")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context); ticket = ticket_or_404(service, ticket_id)
        if status not in TICKET_STATUSES or priority not in TICKET_PRIORITIES or ticket_type not in TICKET_TYPES:
            raise HTTPException(status_code=400, detail="Invalid ticket status, priority, or type")
        resolved_assignee = parse_optional_int(assigned_user_id)
        assignable_users = service.assignable_users()
        valid_users = {item.id for item in assignable_users}
        new_assignee = next((item for item in assignable_users if item.id == resolved_assignee), None)
        if resolved_assignee and resolved_assignee not in valid_users:
            raise HTTPException(status_code=400, detail="Invalid ticket assignment")
        selected_email_profile_id = parse_optional_int(email_profile_id)
        selected_sms_profile_id = parse_optional_int(sms_profile_id)
        profile_service = CommunicationProfileService(db, context)
        valid_email_profiles = {item.id for item in profile_service.available(ticket.owning_organization_id, "email")}
        valid_sms_profiles = {item.id for item in profile_service.available(ticket.owning_organization_id, "sms")}
        if selected_email_profile_id and selected_email_profile_id not in valid_email_profiles:
            raise HTTPException(status_code=400, detail="Invalid email communication profile")
        if selected_sms_profile_id and selected_sms_profile_id not in valid_sms_profiles:
            raise HTTPException(status_code=400, detail="Invalid SMS communication profile")
        old_status = ticket.status
        changes = []
        for label, old, new in (("Status", ticket.status, status), ("Priority", ticket.priority, priority),
                                ("Type", ticket.ticket_type, ticket_type)):
            if old != new: changes.append(f"{label}: {old.replace('_', ' ').title()} → {new.replace('_', ' ').title()}")
        assignment_changed = ticket.assigned_user_id != resolved_assignee
        if assignment_changed: changes.append("Assignment updated")
        if ticket.email_profile_id != selected_email_profile_id: changes.append("Email profile updated")
        if ticket.sms_profile_id != selected_sms_profile_id: changes.append("SMS profile updated")
        ticket.status = status; ticket.priority = priority; ticket.ticket_type = ticket_type
        ticket.assigned_user_id = resolved_assignee; ticket.due_at = parse_datetime(due_at)
        ticket.email_profile_id = selected_email_profile_id; ticket.sms_profile_id = selected_sms_profile_id
        ticket.subject = subject.strip(); ticket.updated_by_user_id = context.user_id
        now = datetime.now(timezone.utc)
        if status == "resolved" and ticket.resolved_at is None: ticket.resolved_at = now
        if status == "closed" and ticket.closed_at is None: ticket.closed_at = now
        if status not in {"resolved", "closed"}: ticket.resolved_at = None; ticket.closed_at = None
        if changes:
            entry = TicketEntry(ticket_id=ticket.id, entry_type="status_change", visibility="customer",
                                body="; ".join(changes), author_user_id=context.user_id)
            db.add(entry); db.flush()
            if old_status != status and settings.ticket_auto_status_notifications:
                event_type = "ticket_resolved" if status == "resolved" else "ticket_status_changed"
                communications = TicketCommunicationService(db)
                messages = communications.queue(
                    ticket, event_type=event_type,
                    message=f"Ticket status changed to {STATUS_LABELS[status]}.", entry=entry,
                    actor_user_id=context.user_id, dedupe_token=f"status-{entry.id}-{status}",
                )
                communications.dispatch_all(messages)
                for outbound in messages:
                    AuditService(db, request, context).record(
                        "tickets.automatic_message", "ticket", ticket.id,
                        f"Automatic {outbound.channel.upper()} {outbound.status}: {event_type}",
                        module="support-tickets", organization_id=ticket.owning_organization_id,
                        event_data={"outbound_message_id": outbound.id},
                    )
            if assignment_changed and new_assignee:
                communications = TicketCommunicationService(db)
                assignment_message = communications.queue_staff_email(
                    ticket, destination=new_assignee.email, event_type="ticket_assigned",
                    message=f"{ticket.ticket_number} has been assigned to you. Priority: {ticket.priority.title()}.",
                    dedupe_token=f"assignment-{entry.id}-{new_assignee.id}", actor_user_id=context.user_id,
                )
                communications.dispatch(assignment_message)
                AuditService(db, request, context).record(
                    "tickets.assignment_message", "ticket", ticket.id,
                    f"Assignment EMAIL {assignment_message.status} to {new_assignee.email}",
                    module="support-tickets", organization_id=ticket.owning_organization_id,
                    event_data={"outbound_message_id": assignment_message.id},
                )
        AuditService(db, request, context).record(
            "tickets.updated", "ticket", ticket.id, "; ".join(changes) or "Ticket updated",
            module="support-tickets", organization_id=ticket.owning_organization_id,
        )
        db.commit()
    return redirect_to_ticket(ticket_id, "Ticket updated.")


@router.post("/{ticket_id}/entries")
def ticket_entry_add(
    request: Request, ticket_id: int, body: str = Form(...), entry_type: str = Form("public_reply"),
    send_email_channel: str | None = Form(None), send_sms_channel: str | None = Form(None),
    sms_consent_override: str | None = Form(None),
):
    permission = "tickets.internal_notes" if entry_type == "internal_note" else "tickets.communicate"
    require_permission(request, permission)
    if entry_type not in {"public_reply", "internal_note"} or not body.strip():
        raise HTTPException(status_code=400, detail="A valid reply or internal note is required")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context); ticket = ticket_or_404(service, ticket_id)
        visibility = "internal" if entry_type == "internal_note" else "customer"
        entry = TicketEntry(ticket_id=ticket.id, entry_type=entry_type, visibility=visibility,
                            body=body.strip(), author_user_id=context.user_id)
        db.add(entry); db.flush()
        messages = []
        if visibility == "customer":
            channels = []
            if send_email_channel: channels.append("email")
            if send_sms_channel: channels.append("sms")
            override = bool(sms_consent_override and context.can("tickets.communication_override"))
            communications = TicketCommunicationService(db)
            messages = communications.queue(
                ticket, event_type="staff_reply", message=body, channels=channels or None,
                entry=entry, actor_user_id=context.user_id, allow_sms_override=override,
            )
            communications.dispatch_all(messages)
            if ticket.source == "third_party_portal" and ticket.created_by and ticket.created_by.active:
                partner_message = communications.queue_staff_email(
                    ticket, destination=ticket.created_by.email, event_type="partner_portal_reply",
                    message=body, dedupe_token=f"partner-reply-{entry.id}-{ticket.created_by.id}",
                    actor_user_id=context.user_id,
                )
                communications.dispatch(partner_message)
                messages.append(partner_message)
                db.add(NotificationEvent(
                    event_type="partner.ticket_staff_reply",
                    subject=f"NTInet replied: {ticket.ticket_number}", payload="{}",
                    recipient_user_id=ticket.created_by.id,
                    organization_id=ticket.created_by.organization_id,
                    channel="internal", status="pending",
                    target_url=f"/partner/tickets/{ticket.id}",
                ))
        ticket.updated_by_user_id = context.user_id
        if ticket.status == "new": ticket.status = "open"
        AuditService(db, request, context).record(
            "tickets.note_added" if visibility == "internal" else "tickets.reply_added",
            "ticket", ticket.id, "Added an internal note" if visibility == "internal" else "Added a customer reply",
            module="support-tickets", organization_id=ticket.owning_organization_id,
        )
        for message in messages:
            AuditService(db, request, context).record(
                "tickets.message_sent" if message.status == "sent" else "tickets.message_not_sent",
                "ticket", ticket.id,
                f"{message.channel.upper()} to {message.destination or 'no destination'}: {message.status}",
                module="support-tickets", organization_id=ticket.owning_organization_id,
                event_data={"outbound_message_id": message.id, "provider_message_id": message.provider_message_id},
            )
        db.commit()
    return redirect_to_ticket(ticket_id, "Internal note added." if visibility == "internal" else "Reply added.")


@router.post("/{ticket_id}/messages/{message_id}/retry")
def ticket_message_retry(request: Request, ticket_id: int, message_id: int):
    require_permission(request, "tickets.retry_messages")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context); ticket = ticket_or_404(service, ticket_id)
        message = db.scalar(select(TicketOutboundMessage).where(
            TicketOutboundMessage.id == message_id, TicketOutboundMessage.ticket_id == ticket.id))
        if message is None: raise HTTPException(status_code=404, detail="Outbound message not found")
        try: TicketCommunicationService(db).retry(message)
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
        AuditService(db, request, context).record(
            "tickets.message_retried", "ticket", ticket.id,
            f"Retried {message.channel.upper()} message; status {message.status}",
            module="support-tickets", organization_id=ticket.owning_organization_id,
        )
        db.commit()
    return redirect_to_ticket(ticket_id, f"Message retry completed: {message.status}.")


@router.post("/{ticket_id}/attachments")
async def ticket_attachment_add(
    request: Request, ticket_id: int, attachment: UploadFile = File(...),
):
    require_permission(request, "tickets.attachments")
    context = context_from_request(request)
    original = Path(attachment.filename or "").name
    suffix = Path(original).suffix.lower()
    if not original or suffix not in ALLOWED_ATTACHMENT_SUFFIXES:
        raise HTTPException(status_code=400, detail="This attachment file type is not allowed")
    content = await attachment.read(settings.ticket_attachment_max_bytes + 1)
    if len(content) > settings.ticket_attachment_max_bytes:
        raise HTTPException(status_code=413, detail="Attachment exceeds the 10 MB limit")
    directory = Path(settings.ticket_attachment_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{suffix}"
    path = directory / stored
    path.write_bytes(content)
    try:
        with SessionLocal() as db:
            service = TicketService(db, context); ticket = ticket_or_404(service, ticket_id)
            record = TicketAttachment(
                ticket_id=ticket.id, original_filename=original, stored_filename=stored,
                content_type=attachment.content_type or "application/octet-stream",
                size_bytes=len(content), uploaded_by_user_id=context.user_id,
            )
            db.add(record)
            AuditService(db, request, context).record(
                "tickets.attachment_added", "ticket", ticket.id, f"Attached {original}",
                module="support-tickets", organization_id=ticket.owning_organization_id,
            )
            db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return redirect_to_ticket(ticket_id, "Attachment uploaded.")


@router.get("/{ticket_id}/attachments/{attachment_id}")
def ticket_attachment_download(request: Request, ticket_id: int, attachment_id: int):
    require_permission(request, "tickets.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = TicketService(db, context); ticket = ticket_or_404(service, ticket_id)
        attachment = db.scalar(select(TicketAttachment).where(
            TicketAttachment.id == attachment_id, TicketAttachment.ticket_id == ticket.id))
        if attachment is None: raise HTTPException(status_code=404, detail="Attachment not found")
        path = Path(settings.ticket_attachment_dir) / attachment.stored_filename
        if not path.is_file(): raise HTTPException(status_code=404, detail="Attachment file is missing")
        filename = attachment.original_filename; media_type = attachment.content_type
    return FileResponse(path, media_type=media_type, filename=filename)
