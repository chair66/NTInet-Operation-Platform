from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, update

from app.database import SessionLocal
from app.database.models import NotificationEvent
from app.security import context_from_request
from app.web import render

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_class=HTMLResponse)
def notification_list(request: Request):
    user_id = context_from_request(request).user_id
    with SessionLocal() as db:
        events = list(db.scalars(select(NotificationEvent).where(
            NotificationEvent.recipient_user_id == user_id,
            NotificationEvent.channel == "internal",
        ).order_by(NotificationEvent.created_at.desc()).limit(250)))
        db.expunge_all()
    return render(request, "notifications/list.html", events=events)

@router.post("/{event_id}/read")
def mark_read(request: Request, event_id: int):
    user_id = context_from_request(request).user_id
    with SessionLocal() as db:
        event = db.scalar(select(NotificationEvent).where(
            NotificationEvent.id == event_id, NotificationEvent.recipient_user_id == user_id,
            NotificationEvent.channel == "internal"))
        if not event: raise HTTPException(404, "Notification not found")
        event.read_at = datetime.now(timezone.utc); target = event.target_url or "/notifications"; db.commit()
    return RedirectResponse(target, status_code=303)

@router.post("/read-all")
def mark_all_read(request: Request):
    user_id = context_from_request(request).user_id
    with SessionLocal() as db:
        db.execute(update(NotificationEvent).where(
            NotificationEvent.recipient_user_id == user_id, NotificationEvent.channel == "internal",
            NotificationEvent.read_at.is_(None)).values(read_at=datetime.now(timezone.utc))); db.commit()
    return RedirectResponse("/notifications", status_code=303)
