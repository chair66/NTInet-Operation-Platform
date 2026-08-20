from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import PortDraft, PortSubmissionAttempt, PortDraftRevision, PortTimelineEvent, PortabilitySnapshot


def _json(value: Any) -> str:
    return json.dumps(value, default=str, separators=(",", ":"))


def values_from_form(form: Any) -> dict[str, Any]:
    values = {str(k): str(v) for k, v in form.items() if k not in {"action"}}
    values["portingAllNumbers"] = "portingAllNumbers" in form
    return values


def reference_for(db: Session) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = db.scalar(select(func.count()).select_from(PortDraft).where(PortDraft.nti_reference.like(f"LNP-{today}-%"))) or 0
    return f"LNP-{today}-{count + 1:06d}"


def save_draft(db: Session, user: Any, values: dict[str, Any], *, draft_id: str | None = None, status: str = "draft", error: dict[str, Any] | None = None) -> PortDraft:
    draft = db.get(PortDraft, draft_id) if draft_id else None
    if draft and draft.organization_id != user.organization_id:
        raise PermissionError("Draft is not available to this organization.")
    if not draft:
        draft = PortDraft(
            id=str(uuid.uuid4()),
            nti_reference=reference_for(db),
            organization_id=user.organization_id,
            created_by_user_id=user.id,
        )
        db.add(draft)
    draft.status = status
    draft.customer_name = str(values.get("customerName") or "")
    draft.billing_telephone_number = str(values.get("billingTelephoneNumber") or "")
    draft.losing_carrier_name = str(values.get("losingCarrierName") or "")
    draft.payload_json = _json(values)
    draft.updated_at = datetime.now(timezone.utc)
    if error:
        draft.last_error_code = str(error.get("code") or "")
        draft.last_error_message = str(error.get("message") or "Submission failed")
    db.flush()
    revision = PortDraftRevision(
        draft_id=draft.id,
        revision_number=len(draft.revisions) + 1,
        event_type="saved",
        summary="Draft updated" if draft.revisions else "Draft created",
        payload_json=draft.payload_json,
        created_by_user_id=getattr(user, "id", None),
    )
    db.add(revision)
    if not draft.timeline_events:
        db.add(PortTimelineEvent(
            draft_id=draft.id, event_type="draft_created", title="Draft created",
            detail=f"Draft {draft.nti_reference} was created.", created_by_user_id=getattr(user, "id", None),
        ))
    db.commit()
    db.refresh(draft)
    return draft


def add_timeline_event(db: Session, draft: PortDraft, event_type: str, title: str, detail: str = "", *, severity: str = "info", data: dict[str, Any] | None = None, user_id: int | None = None) -> PortTimelineEvent:
    event = PortTimelineEvent(draft_id=draft.id, event_type=event_type, title=title, detail=detail, severity=severity, event_data_json=_json(data or {}), created_by_user_id=user_id)
    db.add(event)
    db.commit()
    return event


def record_portability_snapshot(db: Session, draft: PortDraft, raw: Any, summary: dict[str, Any], *, changed: bool, change_summary: str = "") -> PortabilitySnapshot:
    snapshot = PortabilitySnapshot(draft_id=draft.id, raw_response_json=_json(raw), summary_json=_json(summary), changed=changed, change_summary=change_summary)
    db.add(snapshot)
    db.commit()
    return snapshot


def record_attempt(db: Session, draft: PortDraft, payload: dict[str, Any], *, success: bool, response: Any = None, error: dict[str, Any] | None = None) -> PortSubmissionAttempt:
    attempt = PortSubmissionAttempt(
        draft_id=draft.id,
        attempt_number=len(draft.attempts) + 1,
        success=success,
        request_json=_json(payload),
        response_json=_json(response or {}),
        error_code=str((error or {}).get("code") or ""),
        error_message=str((error or {}).get("message") or ""),
    )
    db.add(attempt)
    db.commit()
    return attempt


def load_values(draft: PortDraft) -> dict[str, Any]:
    try:
        result = json.loads(draft.payload_json or "{}")
        return result if isinstance(result, dict) else {}
    except (TypeError, ValueError):
        return {}
