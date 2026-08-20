from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import NotificationEvent, PortDraft
from app.services.notifications import render_email_template, send_port_email


def _ci(data: dict[str, Any], *keys: str) -> Any:
    targets = {str(k).casefold() for k in keys}
    for key, value in (data or {}).items():
        if str(key).casefold() in targets:
            return value
    return None


def _clean_status(value: Any) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def _numbers(order: dict[str, Any]) -> list[str]:
    value = _ci(order, "phoneNumbers", "telephoneNumbers", "listOfPhoneNumbers") or []
    if isinstance(value, dict):
        for key in ("telephoneNumber", "phoneNumber", "Tn", "tn"):
            nested = _ci(value, key)
            if nested not in (None, ""):
                value = nested
                break
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v or "").strip()]


def _flatten_notes(value: Any) -> list[str]:
    result: list[str] = []
    if value in (None, ""):
        return result
    if isinstance(value, str):
        text = value.strip()
        if text:
            result.append(text)
        return result
    if isinstance(value, list):
        for item in value:
            result.extend(_flatten_notes(item))
        return result
    if isinstance(value, dict):
        # Prefer human-readable note/comment/message fields over IDs/timestamps.
        for key in ("note", "notes", "comment", "comments", "message", "description", "text", "detail", "reason"):
            nested = _ci(value, key)
            if nested not in (None, ""):
                result.extend(_flatten_notes(nested))
        return result
    return result


def _provider_note(order: dict[str, Any]) -> str:
    notes: list[str] = []
    for key in (
        "notes", "note", "comments", "comment", "messages", "message",
        "statusMessage", "statusDescription", "exceptionMessage", "exception",
        "errors", "errorList",
    ):
        value = _ci(order, key)
        if value not in (None, ""):
            notes.extend(_flatten_notes(value))
    # Stable de-duplication while preserving provider order.
    seen: set[str] = set()
    cleaned: list[str] = []
    for item in notes:
        text = " ".join(str(item).split())
        if text and text not in seen:
            seen.add(text)
            cleaned.append(text)
    return " | ".join(cleaned)


def _state(draft: PortDraft) -> dict[str, Any]:
    try:
        value = json.loads(draft.notification_state_json or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def _save_state(draft: PortDraft, state: dict[str, Any]) -> None:
    draft.notification_state_json = json.dumps(state, sort_keys=True, default=str)


def _event_for_status(status: str, order: dict[str, Any]) -> str | None:
    text = _clean_status(status)
    if "EXCEPTION" in text or text in {"FAILED", "REJECTED", "ERROR"}:
        return "exception"
    if text.startswith("COMPLETE") or text in {"COMPLETED", "COMPLETE", "PORTED"}:
        return "completed"
    foc = _ci(order, "actualFocDate", "ActualFocDate", "focDate", "FocDate")
    if foc not in (None, "") or text in {"FOC", "FOC_RECEIVED", "FOC_CONFIRMED"}:
        return "foc"
    return None




def _notification_timezone(draft: PortDraft) -> tuple[object, str]:
    """Return the submitter/account timezone used for customer-facing port emails.

    NOP users currently inherit timezone from their organization account. Prefer the
    submitting user's organization, then the draft organization, and fall back to
    America/New_York for legacy records.
    """
    submitter = getattr(draft, "submitted_by", None) or getattr(draft, "created_by", None)
    org = getattr(submitter, "organization", None) or getattr(draft, "organization", None)
    name = str(getattr(org, "timezone", "") or "America/New_York").strip()
    try:
        return ZoneInfo(name), name
    except (ZoneInfoNotFoundError, ValueError):
        try:
            return ZoneInfo("America/New_York"), "America/New_York"
        except ZoneInfoNotFoundError:
            return timezone.utc, "UTC"


def _format_provider_datetime(value: Any, draft: PortDraft) -> str:
    """Render an ISO provider timestamp in the submitter's account timezone."""
    text = str(value or "").strip()
    if not text:
        return "Not provided"
    candidate = text
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text
    if parsed.tzinfo is None:
        # Provider timestamps without an offset are treated as UTC, matching the
        # Bandwidth ISO values returned elsewhere in the porting workflow.
        parsed = parsed.replace(tzinfo=timezone.utc)
    tz, _tz_name = _notification_timezone(draft)
    local = parsed.astimezone(tz)
    zone_label = local.tzname() or _tz_name
    hour = local.strftime("%I").lstrip("0") or "0"
    return f"{local.strftime('%B')} {local.day}, {local.year} at {hour}:{local.strftime('%M')} {local.strftime('%p')} {zone_label}"

def _friendly(value: Any) -> str:
    return str(value or "").strip() or "Not provided"


def _subject_and_body(event: str, draft: PortDraft, order: dict[str, Any], *, order_url: str, provider_note: str) -> tuple[str, str]:
    status = _clean_status(_ci(order, "processingStatus", "ProcessingStatus", "status") or draft.bandwidth_status)
    order_id = str(_ci(order, "orderId", "OrderId", "id") or draft.bandwidth_order_id or "")
    tns = ", ".join(_numbers(order)) or _friendly(draft.billing_telephone_number)
    common = dict(
        nti_reference=draft.nti_reference,
        customer_name=draft.customer_name or "Not entered",
        order_id=order_id,
        status=status or "Unknown",
        phone_numbers=tns,
        provider_note=provider_note or "No provider note was included.",
        order_url=order_url,
    )
    if event == "exception":
        return (
            f"Port Exception - {draft.nti_reference}",
            render_email_template("port_exception.html", exception_message=common["provider_note"], **common),
        )
    if event == "foc":
        foc = _ci(order, "actualFocDate", "ActualFocDate", "focDate", "FocDate", "requestedFocDate")
        return (
            f"Port FOC Confirmed - {draft.nti_reference}",
            render_email_template("port_foc.html", foc_date=_format_provider_datetime(foc, draft), **common),
        )
    if event == "completed":
        completed = _ci(order, "completionDate", "completedDate", "CompletedDate", "lastModifiedDate")
        return (
            f"Port Completed - {draft.nti_reference}",
            render_email_template("port_completed.html", completed_date=_format_provider_datetime(completed, draft), **common),
        )
    return (
        f"Port Update - {draft.nti_reference}",
        render_email_template("port_note.html", **common),
    )


def process_port_notification(db: Session, order: dict[str, Any], *, order_url: str = "") -> list[str]:
    """Send de-duplicated status/note email updates for a tracked Bandwidth port.

    Returns a list of event names sent in this invocation. Repeated provider reads do
    not resend the same status or identical provider note.
    """
    order_id = str(_ci(order, "orderId", "OrderId", "id") or "").strip()
    if not order_id:
        return []
    draft = db.scalar(select(PortDraft).where(PortDraft.bandwidth_order_id == order_id))
    if draft is None or not draft.notifications_enabled:
        return []
    recipient = str(draft.notification_email or "").strip()
    if not recipient:
        submitter = getattr(draft, "submitted_by", None) or getattr(draft, "created_by", None)
        recipient = str(getattr(submitter, "email", "") or "").strip()
        if recipient:
            draft.notification_email = recipient
    if not recipient:
        return []

    state = _state(draft)
    current_status = _clean_status(_ci(order, "processingStatus", "ProcessingStatus", "status") or draft.bandwidth_status)
    provider_note = _provider_note(order)
    note_hash = hashlib.sha256(provider_note.encode("utf-8")).hexdigest() if provider_note else ""
    event = _event_for_status(current_status, order)
    sent: list[str] = []

    if event and state.get("last_status_event") != event:
        subject, body = _subject_and_body(event, draft, order, order_url=order_url, provider_note=provider_note)
        if send_port_email(subject, body, [recipient]):
            state["last_status_event"] = event
            state["last_status"] = current_status
            state["last_status_sent_at"] = datetime.now().astimezone().isoformat()
            sent.append(event)
            db.add(NotificationEvent(
                organization_id=draft.organization_id, actor_user_id=None, recipient_user_id=draft.submitted_by_user_id,
                event_type=f"port.{event}", channel="email", subject=subject,
                payload=json.dumps({"order_id": order_id, "recipient": recipient, "status": current_status}, sort_keys=True),
                status="sent", processed_at=datetime.now().astimezone(),
            ))

    # Notify on other provider status changes too (for example pending/processing),
    # while avoiding a duplicate when a specialized Exception/FOC/Completed email was sent.
    previous_status = str(state.get("last_status") or "").strip().upper()
    if current_status and current_status != previous_status and not sent and current_status not in {"SUBMITTED", "DRAFT"}:
        subject, body = _subject_and_body("note", draft, order, order_url=order_url, provider_note=provider_note or f"Status changed to {current_status}.")
        subject = f"Port Status Update - {draft.nti_reference}"
        if send_port_email(subject, body, [recipient]):
            state["last_status"] = current_status
            state["last_status_sent_at"] = datetime.now().astimezone().isoformat()
            sent.append("status")
            db.add(NotificationEvent(
                organization_id=draft.organization_id, actor_user_id=None, recipient_user_id=draft.submitted_by_user_id,
                event_type="port.status", channel="email", subject=subject,
                payload=json.dumps({"order_id": order_id, "recipient": recipient, "status": current_status}, sort_keys=True),
                status="sent", processed_at=datetime.now().astimezone(),
            ))

    if provider_note and note_hash != state.get("last_provider_note_hash"):
        # If the new note was already included in a status email in this invocation,
        # remember it but do not send a duplicate note-only email.
        if sent:
            state["last_provider_note_hash"] = note_hash
        else:
            subject, body = _subject_and_body("note", draft, order, order_url=order_url, provider_note=provider_note)
            if send_port_email(subject, body, [recipient]):
                state["last_provider_note_hash"] = note_hash
                state["last_note_sent_at"] = datetime.now().astimezone().isoformat()
                sent.append("note")
                db.add(NotificationEvent(
                    organization_id=draft.organization_id, actor_user_id=None, recipient_user_id=draft.submitted_by_user_id,
                    event_type="port.note", channel="email", subject=subject,
                    payload=json.dumps({"order_id": order_id, "recipient": recipient, "status": current_status, "provider_note": provider_note}, sort_keys=True),
                    status="sent", processed_at=datetime.now().astimezone(),
                ))

    if current_status:
        draft.bandwidth_status = current_status
    _save_state(draft, state)
    return sent
