from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.job_models import Job, JobCommunicationEvent
from app.services.customer_communication_service import CustomerCommunicationService


settings = get_settings()


@dataclass(slots=True)
class JobCommunicationService:
    db: Session

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

    @staticmethod
    def _contact(job: Job):
        candidates = (job.contact, job.location.primary_contact, job.customer.primary_contact)
        return next((item for item in candidates if item and item.active), None)

    @staticmethod
    def _local_time(job: Job) -> datetime | None:
        if not job.scheduled_start: return None
        try: zone = ZoneInfo(job.location.timezone or settings.app_timezone)
        except ZoneInfoNotFoundError: zone = ZoneInfo(settings.app_timezone)
        return JobCommunicationService._aware(job.scheduled_start).astimezone(zone)

    def _cancel_pending(self, job: Job, reason: str) -> None:
        for event in self.db.scalars(select(JobCommunicationEvent).where(
            JobCommunicationEvent.job_id == job.id,
            JobCommunicationEvent.status == "queued",
        )):
            event.status = "cancelled"; event.processed_at = datetime.now(timezone.utc)
            event.error_message = reason

    def _queue(self, job: Job, event_type: str, channel: str, scheduled_for: datetime,
               actor_user_id: int | None) -> JobCommunicationEvent | None:
        token_time = self._aware(job.scheduled_start).isoformat() if job.scheduled_start else datetime.now(timezone.utc).isoformat()
        key = f"job:{job.id}:{event_type}:{channel}:{token_time}"
        existing = self.db.scalar(select(JobCommunicationEvent).where(
            JobCommunicationEvent.deduplication_key == key))
        if existing: return None
        event = JobCommunicationEvent(job_id=job.id,event_type=event_type,channel=channel,
            status="queued",deduplication_key=key,scheduled_for=scheduled_for,
            created_by_user_id=actor_user_id)
        self.db.add(event); self.db.flush(); return event

    def schedule_changed(self, job: Job, *, rescheduled: bool, actor_user_id: int | None) -> list[JobCommunicationEvent]:
        if not settings.job_scheduling_communications_enabled or not job.scheduled_start: return []
        self._cancel_pending(job,"Superseded by a new appointment schedule.")
        now=datetime.now(timezone.utc); created=[]
        event_type="appointment_rescheduled" if rescheduled else "appointment_scheduled"
        if settings.job_appointment_email_enabled:
            item=self._queue(job,event_type,"email",now,actor_user_id)
            if item: created.append(item)
        if settings.job_appointment_sms_enabled:
            item=self._queue(job,event_type,"sms",now,actor_user_id)
            if item: created.append(item)
        reminder_at=self._aware(job.scheduled_start)-timedelta(hours=max(1,settings.job_reminder_hours))
        if reminder_at > now:
            if settings.job_appointment_email_enabled:
                item=self._queue(job,"appointment_reminder","email",reminder_at,actor_user_id)
                if item: created.append(item)
            if settings.job_appointment_sms_enabled:
                item=self._queue(job,"appointment_reminder","sms",reminder_at,actor_user_id)
                if item: created.append(item)
        self.process_due(job_id=job.id)
        return created

    def appointment_cancelled(self, job: Job, *, actor_user_id: int | None) -> list[JobCommunicationEvent]:
        if not settings.job_scheduling_communications_enabled: return []
        self._cancel_pending(job,"Appointment was cancelled.")
        now=datetime.now(timezone.utc); created=[]
        for channel,enabled in (("email",settings.job_appointment_email_enabled),("sms",settings.job_appointment_sms_enabled)):
            if enabled:
                item=self._queue(job,"appointment_cancelled",channel,now,actor_user_id)
                if item: created.append(item)
        self.process_due(job_id=job.id); return created

    def technician_en_route(self, job: Job, *, actor_user_id: int | None) -> list[JobCommunicationEvent]:
        if not settings.job_scheduling_communications_enabled or not settings.job_en_route_notification_enabled: return []
        now=datetime.now(timezone.utc); created=[]
        for channel,enabled in (("email",settings.job_appointment_email_enabled),("sms",settings.job_appointment_sms_enabled)):
            if enabled:
                item=self._queue(job,"technician_en_route",channel,now,actor_user_id)
                if item: created.append(item)
        self.process_due(job_id=job.id); return created

    def _content(self, event: JobCommunicationEvent) -> tuple[str,str]:
        job=event.job; local_time=self._local_time(job)
        when=local_time.strftime("%A, %B %d at %I:%M %p") if local_time else "the scheduled time"
        address=job.location.one_line_address
        subjects={
            "appointment_scheduled":"Your NTInet service appointment is scheduled",
            "appointment_rescheduled":"Your NTInet service appointment was updated",
            "appointment_reminder":"Reminder: upcoming NTInet service appointment",
            "appointment_cancelled":"Your NTInet service appointment was cancelled",
            "technician_en_route":"Your NTInet technician is on the way",
        }
        if event.event_type=="appointment_cancelled":
            body=f"Your NTInet service appointment for {job.summary} has been cancelled. Please reply or contact NTInet if you need to reschedule. Reference {job.job_number}."
        elif event.event_type=="technician_en_route":
            body=f"Your NTInet technician is on the way to {address} for {job.summary}. Reference {job.job_number}."
        else:
            lead={"appointment_scheduled":"Your NTInet service appointment is scheduled",
                  "appointment_rescheduled":"Your NTInet service appointment has been rescheduled",
                  "appointment_reminder":"This is a reminder of your NTInet service appointment"}[event.event_type]
            body=f"{lead} for {when} at {address}. Work: {job.summary}. Reference {job.job_number}."
        return subjects[event.event_type],body

    def dispatch(self, event: JobCommunicationEvent) -> JobCommunicationEvent:
        if event.status != "queued": return event
        contact=self._contact(event.job); now=datetime.now(timezone.utc)
        if not contact:
            event.status="suppressed"; event.error_message="No active customer contact is available."
            event.processed_at=now; return event
        subject,body=self._content(event)
        communication=CustomerCommunicationService(self.db).send(
            event.job.customer,contact_id=contact.id,channel=event.channel,
            subject=subject if event.channel=="email" else "",body=body,profile_id=None,
            ticket_id=event.job.ticket_id,consent_override=False,override_reason="",
            actor_user_id=event.created_by_user_id or event.job.updated_by_user_id or event.job.created_by_user_id,
            module_slug="field-service")
        event.customer_communication_id=communication.id
        event.status=communication.status; event.error_message=communication.error_message
        event.processed_at=now
        return event

    def process_due(self, *, limit: int = 200, job_id: int | None = None) -> list[JobCommunicationEvent]:
        now=datetime.now(timezone.utc)
        statement=select(JobCommunicationEvent).where(
            JobCommunicationEvent.status=="queued",JobCommunicationEvent.scheduled_for<=now)
        if job_id: statement=statement.where(JobCommunicationEvent.job_id==job_id)
        events=list(self.db.scalars(statement.order_by(JobCommunicationEvent.scheduled_for).limit(limit)).unique())
        for event in events:
            try: self.dispatch(event)
            except Exception as exc:
                event.status="failed"; event.error_message=str(exc)[:2000]; event.processed_at=now
        return events
