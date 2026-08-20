from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
import secrets

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select, update

from app.config import get_settings
from app.database import SessionLocal
from app.database.customer_models import Customer, CustomerContact
from app.database.models import NotificationEvent
from app.database.ticket_models import TicketAttachment, TicketEntry
from app.security import context_from_request
from app.security.passwords import hash_password, verify_password
from app.services import AuditService
from app.services.partner_portal_service import PartnerPortalService
from app.services.ticket_service import TICKET_PRIORITIES, TICKET_TYPES
from app.services.ticket_communications import normalize_us_number
from app.web import render


router = APIRouter(prefix="/partner", tags=["Third-Party Support Portal"])
settings = get_settings()
ALLOWED_ATTACHMENT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".log", ".csv", ".doc", ".docx", ".xls", ".xlsx"}
STATUS_LABELS = {"new": "New", "open": "Open", "pending_customer": "Waiting on Customer", "scheduled": "Scheduled", "resolved": "Resolved", "closed": "Closed"}
TYPE_LABELS = {
    "no_internet_all_devices": "No Internet — All Devices",
    "no_internet_single_device": "No Internet — Single Device",
    "billing": "Billing", "phone": "Phone", "service_request": "Service Request", "other": "Other",
}
AFFECTED_SERVICE_ISSUES = {
    "internet": [("no_internet_all_devices", "No Internet — All Devices"),
                 ("no_internet_single_device", "No Internet — Single Device"),
                 ("internet_slow", "Slow Speeds"),
                 ("internet_intermittent", "Intermittent Connection"),
                 ("internet_wifi", "Wi-Fi Issue"), ("internet_other", "Other Internet Issue")],
    "phone": [("phone_no_dial_tone", "No Dial Tone"),
              ("phone_inbound", "Cannot Receive Calls"),
              ("phone_outbound", "Cannot Make Calls"), ("phone_quality", "Call Quality"),
              ("phone_voicemail", "Voicemail"), ("phone_other", "Other Phone Issue")],
    "email": [("email_send_receive", "Cannot Send or Receive"),
              ("email_login", "Login or Password"), ("email_spam", "Spam or Filtering"),
              ("email_setup", "Device Setup"), ("email_other", "Other Email Issue")],
    "billing": [("billing_question", "Account Question"), ("billing_payment", "Payment"),
                ("billing_charge", "Charge or Invoice"), ("billing_other", "Other Billing Issue")],
    "other": [("service_request", "Service Request"), ("other", "Other")],
}
PRIORITY_LABELS = {"low": "Low", "normal": "Normal", "high": "High", "urgent": "Urgent"}


def service_for(request: Request, db) -> PartnerPortalService:
    context = context_from_request(request)
    if not (context.is_support_partner and context.can("partner_portal.access")):
        raise HTTPException(403, "Third-party support portal access is required")
    return PartnerPortalService(db, context)


def optional_int(value: str | None) -> int | None:
    try:
        return int(value) if value and value.strip() else None
    except ValueError as exc:
        raise HTTPException(400, "Invalid selection") from exc


def redirect_ticket(ticket_id: int, message: str = "") -> RedirectResponse:
    suffix = f"?message={quote(message)}" if message else ""
    return RedirectResponse(f"/partner/tickets/{ticket_id}{suffix}", status_code=303)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def portal_home(request: Request, customer_q: str = "", customer_id: int | None = None):
    with SessionLocal() as db:
        service = service_for(request, db)
        customer_results = service.search_customers(customer_q, limit=25) if customer_q.strip() else []
        selected_customer = service.customer_profile(customer_id) if customer_id else None
        current_tickets = service.customer_tickets(customer_id) if selected_customer else []
        recent_tickets = service.customer_tickets(customer_id, closed=True) if selected_customer else []
        for ticket in current_tickets + recent_tickets:
            _ = ticket.customer.name
        db.expunge_all()
    return render(request, "partner/list.html", current_tickets=current_tickets,
                  recent_tickets=recent_tickets, customer_results=customer_results,
                  selected_customer=selected_customer, customer_q=customer_q,
                  status_labels=STATUS_LABELS,
                  partner_layout=True)


@router.get("/tickets/new", response_class=HTMLResponse)
def new_ticket(request: Request, customer_id: int | None = None):
    with SessionLocal() as db:
        service = service_for(request, db)
        initial_customer = service.customer_options(customer_id) if customer_id else None
    return render(request, "partner/new_ticket.html", type_labels=TYPE_LABELS,
                  priority_labels=PRIORITY_LABELS, initial_customer=initial_customer,
                  affected_service_issues=AFFECTED_SERVICE_ISSUES,
                  partner_layout=True)


@router.post("/contact-verification/send")
def partner_contact_verification_send(
    request: Request, customer_id: int = Form(...), channel: str = Form(...),
    destination: str = Form(...),
):
    from app.routers.tickets import valid_email_address, send_email_verification, send_contact_verification
    if channel not in {"email", "mobile"}:
        raise HTTPException(400, "Choose email or mobile verification.")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = service_for(request, db)
        if service.customer_profile(customer_id) is None:
            raise HTTPException(404, "Customer not found or unavailable.")
        customer = db.get(Customer, customer_id)
        normalized = valid_email_address(destination) if channel == "email" else normalize_us_number(destination)
        if not normalized:
            raise HTTPException(400, f"Enter a valid {'email address' if channel == 'email' else '10-digit US mobile number'}.")
        event_type = f"tickets.{channel}_verification"
        if channel == "mobile":
            event_type = "tickets.mobile_verification"
        recent = db.scalar(select(NotificationEvent).where(
            NotificationEvent.event_type == event_type,
            NotificationEvent.actor_user_id == context.user_id,
            NotificationEvent.created_at >= datetime.now(timezone.utc) - timedelta(seconds=60),
        ).order_by(NotificationEvent.created_at.desc()))
        if recent:
            raise HTTPException(429, "Please wait 60 seconds before sending another verification message.")
        token = secrets.token_urlsafe(32)
        event = NotificationEvent(
            organization_id=customer.owner_organization_id, actor_user_id=context.user_id,
            event_type=event_type, channel="email" if channel == "email" else "sms",
            subject=f"Verify {normalized}", status="sending",
            payload=json.dumps({"customer_id": customer.id, "destination": normalized,
                                "token_hash": hashlib.sha256(token.encode()).hexdigest()}, sort_keys=True),
        )
        db.add(event); db.flush()
        confirmation_url = (
            f"{settings.ticket_public_base_url.rstrip('/')}/tickets/contact-verification/"
            f"{channel}/confirm/{event.id}/{token}"
        )
        try:
            if channel == "email":
                send_email_verification(db, customer.owner_organization_id, normalized, confirmation_url)
            else:
                send_contact_verification(db, customer.owner_organization_id, normalized,
                                          confirmation_url, f"nop:partner-verification:{customer.id}")
        except (RuntimeError, ValueError) as exc:
            event.status = "failed"; db.commit()
            raise HTTPException(400, str(exc)) from exc
        event.status = "sent"; db.commit()
        return {"ok": True, "destination": normalized, "verification_id": event.id,
                "message": f"Verification {'email' if channel == 'email' else 'text'} sent. Waiting for confirmation."}


@router.post("/contact-verification/{channel}/status")
def partner_contact_verification_status(
    request: Request, channel: str, verification_id: str = Form(""),
    customer_id: int = Form(...), destination: str = Form(...),
):
    from app.routers.tickets import valid_email_address
    if channel not in {"email", "mobile"}:
        raise HTTPException(400, "Invalid verification channel.")
    context = context_from_request(request)
    normalized = valid_email_address(destination) if channel == "email" else normalize_us_number(destination)
    if not normalized:
        raise HTTPException(400, "Enter a valid destination.")
    try:
        event_id = int(verification_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(404, "Verification request not found.") from exc
    with SessionLocal() as db:
        service_for(request, db)
        event = db.get(NotificationEvent, event_id)
        expected_type = "tickets.email_verification" if channel == "email" else "tickets.mobile_verification"
        if not event or event.event_type != expected_type or event.actor_user_id != context.user_id:
            raise HTTPException(404, "Verification request not found.")
        payload = json.loads(event.payload or "{}")
        if int(payload.get("customer_id", 0)) != customer_id or payload.get("destination") != normalized:
            raise HTTPException(400, "The verification request no longer matches this ticket.")
        if datetime.now(timezone.utc) > event.created_at + timedelta(minutes=30) and event.status not in {"confirmed", "consumed"}:
            event.status = "expired"; db.commit()
        return {"confirmed": event.status in {"confirmed", "consumed"}, "status": event.status,
                "destination": normalized, "verification_id": event.id}


@router.get("/password", response_class=HTMLResponse)
def partner_password(request: Request, notice: str = "", error: str = ""):
    with SessionLocal() as db:
        service_for(request, db)
    return render(request, "partner/password.html", notice=notice, error=error, partner_layout=True)


@router.post("/password")
def partner_password_change(request: Request, current_password: str = Form(...),
                            new_password: str = Form(...), confirm_password: str = Form(...)):
    context = context_from_request(request)
    if new_password != confirm_password:
        return RedirectResponse("/partner/password?error=The+new+passwords+do+not+match", status_code=303)
    if len(new_password) < 12:
        return RedirectResponse("/partner/password?error=The+new+password+must+be+at+least+12+characters", status_code=303)
    if current_password == new_password:
        return RedirectResponse("/partner/password?error=The+new+password+must+be+different", status_code=303)
    with SessionLocal() as db:
        service_for(request, db)
        user = db.get(type(context.user), context.user_id)
        if not verify_password(current_password, user.password_hash):
            return RedirectResponse("/partner/password?error=Your+current+password+was+not+accepted", status_code=303)
        user.password_hash = hash_password(new_password)
        user.force_password_change = False
        user.password_changed_at = datetime.now(timezone.utc)
        AuditService(db, request, context).record(
            "account.password_changed", "user", user.id,
            "Password changed through third-party support portal", module="identity",
            organization_id=context.organization_id,
        )
        db.commit()
    return RedirectResponse("/partner?message=Password+changed+successfully", status_code=303)


@router.get("/customers/search")
def customer_search(request: Request, q: str = ""):
    with SessionLocal() as db:
        results = service_for(request, db).search_customers(q)
    return JSONResponse({"results": results})


@router.get("/customers/{customer_id}/options")
def customer_options(request: Request, customer_id: int):
    with SessionLocal() as db:
        result = service_for(request, db).customer_options(customer_id)
    if result is None:
        raise HTTPException(404, "Customer not found")
    return JSONResponse(result)


@router.post("/tickets")
def create_ticket(request: Request, customer_id: int = Form(...), contact_id: str = Form(""),
                  location_id: str = Form(""), subject: str = Form(...),
                  description: str = Form(...), ticket_type: str = Form("no_internet_all_devices"),
                  priority: str = Form("normal"), affected_service: str = Form("internet"),
                  callback_number: str = Form(""), correspondence_mode: str = Form("account"),
                  correspondence_email: str = Form(""), correspondence_email_code: str = Form(""),
                  correspondence_mobile: str = Form(""), correspondence_mobile_code: str = Form(""),
                  save_to_account_contact: str | None = Form(None)):
    context = context_from_request(request)
    with SessionLocal() as db:
        service = service_for(request, db)
        try:
            if correspondence_mode not in {"account", "additional"}:
                raise ValueError("Choose a valid correspondence option.")
            valid_issues = {value for value, _label in AFFECTED_SERVICE_ISSUES.get(affected_service, [])}
            if ticket_type not in valid_issues:
                raise ValueError("Select a valid issue for the affected service.")
            normalized_callback = normalize_us_number(callback_number) if callback_number.strip() else ""
            if callback_number.strip() and not normalized_callback:
                raise ValueError("Callback number must be a valid 10-digit US telephone number.")
            verified_email = verified_mobile = ""
            email_event = mobile_event = None
            selected_contact_id = optional_int(contact_id)
            update_account_contact = bool(save_to_account_contact)
            if update_account_contact and not selected_contact_id:
                raise ValueError("Select an account contact before saving verified information to the account.")
            if update_account_contact and correspondence_mode != "additional":
                raise ValueError("Choose additional correspondence before updating the account contact.")
            if correspondence_mode == "additional":
                if not correspondence_email.strip() and not correspondence_mobile.strip():
                    raise ValueError("Enter and verify an additional email address or mobile number.")
                from app.routers.tickets import verify_new_ticket_destination
                verified_email, email_event = verify_new_ticket_destination(
                    request, db, customer_id, "email", correspondence_email, correspondence_email_code)
                verified_mobile, mobile_event = verify_new_ticket_destination(
                    request, db, customer_id, "mobile", correspondence_mobile, correspondence_mobile_code)
            ticket = service.create_ticket(
                customer_id=customer_id, contact_id=selected_contact_id, location_id=optional_int(location_id),
                service_id=None, subject=subject, description=description,
                ticket_type=ticket_type, priority=priority,
            )
            for entry_type, value in (("callback_number", normalized_callback),
                                      ("correspondence_email", verified_email),
                                      ("correspondence_mobile", verified_mobile)):
                if value:
                    db.add(TicketEntry(ticket_id=ticket.id, entry_type=entry_type,
                                       visibility="internal", body=value,
                                       author_user_id=context.user_id))
            if update_account_contact:
                account_contact = db.get(CustomerContact, selected_contact_id)
                if account_contact is None or account_contact.customer_id != customer_id or not account_contact.active:
                    raise ValueError("The selected contact is not available for this customer.")
                updated_fields = []
                if verified_email:
                    account_contact.email = verified_email
                    updated_fields.append("email address")
                if verified_mobile:
                    account_contact.mobile_phone = verified_mobile
                    updated_fields.append("mobile number")
                if not updated_fields:
                    raise ValueError("Confirm an additional email address or mobile number before updating the contact.")
                db.add(TicketEntry(
                    ticket_id=ticket.id, entry_type="account_contact_update", visibility="internal",
                    body=f"Verified and updated {' and '.join(updated_fields)} on account contact {account_contact.full_name} through the third-party support portal.",
                    author_user_id=context.user_id,
                ))
            for event in (email_event, mobile_event):
                if event:
                    event.status = "consumed"
            AuditService(db, request, context).record(
                "partner.ticket_created", "ticket", ticket.id,
                f"Third-party portal created {ticket.ticket_number}", module="support-tickets",
                organization_id=ticket.owning_organization_id,
                event_data={"partner_organization_id": context.organization_id},
            )
            db.commit(); ticket_id = ticket.id
        except ValueError as exc:
            db.rollback(); raise HTTPException(400, str(exc)) from exc
    return redirect_ticket(ticket_id, "Ticket submitted to NTInet support.")


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(request: Request, ticket_id: int, message: str = ""):
    context = context_from_request(request)
    with SessionLocal() as db:
        ticket = service_for(request, db).get_ticket(ticket_id)
        if ticket is None:
            raise HTTPException(404, "Ticket not found")
        db.execute(update(NotificationEvent).where(
            NotificationEvent.recipient_user_id == context.user_id,
            NotificationEvent.target_url == f"/partner/tickets/{ticket.id}",
            NotificationEvent.read_at.is_(None),
        ).values(read_at=datetime.now(timezone.utc)))
        db.commit()
        _ = tuple(ticket.entries); _ = tuple(ticket.attachments)
        db.expunge_all()
    return render(request, "partner/detail.html", ticket=ticket, message=message, status_labels=STATUS_LABELS, priority_labels=PRIORITY_LABELS, partner_layout=True)


@router.post("/tickets/{ticket_id}/replies")
def add_reply(request: Request, ticket_id: int, body: str = Form(...)):
    context = context_from_request(request)
    with SessionLocal() as db:
        service = service_for(request, db); ticket = service.get_ticket(ticket_id)
        if ticket is None:
            raise HTTPException(404, "Ticket not found")
        try:
            service.add_reply(ticket, body)
            AuditService(db, request, context).record(
                "partner.ticket_reply", "ticket", ticket.id, "Third-party portal reply added",
                module="support-tickets", organization_id=ticket.owning_organization_id,
            )
            db.commit()
        except ValueError as exc:
            db.rollback(); raise HTTPException(400, str(exc)) from exc
    return redirect_ticket(ticket_id, "Reply sent to NTInet support.")


@router.post("/tickets/{ticket_id}/attachments")
async def add_attachment(request: Request, ticket_id: int, attachment: UploadFile = File(...)):
    context = context_from_request(request)
    original = Path(attachment.filename or "").name
    suffix = Path(original).suffix.lower()
    if not original or suffix not in ALLOWED_ATTACHMENT_SUFFIXES:
        raise HTTPException(400, "This attachment file type is not allowed")
    content = await attachment.read(settings.ticket_attachment_max_bytes + 1)
    if len(content) > settings.ticket_attachment_max_bytes:
        raise HTTPException(413, "Attachment exceeds the 10 MB limit")
    directory = Path(settings.ticket_attachment_dir); directory.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{suffix}"; path = directory / stored; path.write_bytes(content)
    try:
        with SessionLocal() as db:
            service = service_for(request, db); ticket = service.get_ticket(ticket_id)
            if ticket is None:
                raise HTTPException(404, "Ticket not found")
            db.add(TicketAttachment(ticket_id=ticket.id, original_filename=original, stored_filename=stored,
                                    content_type=attachment.content_type or "application/octet-stream",
                                    size_bytes=len(content), uploaded_by_user_id=context.user_id))
            AuditService(db, request, context).record("partner.ticket_attachment", "ticket", ticket.id,
                f"Third-party attachment: {original}", module="support-tickets", organization_id=ticket.owning_organization_id)
            db.commit()
    except Exception:
        path.unlink(missing_ok=True); raise
    return redirect_ticket(ticket_id, "Attachment uploaded.")


@router.get("/tickets/{ticket_id}/attachments/{attachment_id}")
def download_attachment(request: Request, ticket_id: int, attachment_id: int):
    with SessionLocal() as db:
        service = service_for(request, db); ticket = service.get_ticket(ticket_id)
        if ticket is None:
            raise HTTPException(404, "Ticket not found")
        item = db.scalar(select(TicketAttachment).where(TicketAttachment.id == attachment_id, TicketAttachment.ticket_id == ticket.id))
        if item is None:
            raise HTTPException(404, "Attachment not found")
        path = Path(settings.ticket_attachment_dir) / item.stored_filename
        if not path.is_file():
            raise HTTPException(404, "Attachment file is missing")
        filename, media_type = item.original_filename, item.content_type
    return FileResponse(path, filename=filename, media_type=media_type)
