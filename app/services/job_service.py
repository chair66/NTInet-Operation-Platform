from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.database.customer_models import Customer, CustomerLocation
from app.database.job_models import Job, JobActivity, JobAssignment
from app.database.models import Organization, User
from app.database.ticket_models import Ticket
from app.security.context import SecurityContext
from app.services.customer_service import CustomerService


JOB_STATUSES = {"unscheduled", "scheduled", "dispatched", "en_route", "on_site", "in_progress", "paused", "completed", "cancelled", "follow_up_required"}
JOB_PRIORITIES = {"low", "normal", "high", "urgent"}
JOB_TYPES = {"service_call", "installation", "repair", "maintenance", "site_survey", "delivery", "other"}
TECHNICIAN_TRANSITIONS = {
    "scheduled": {"en_route", "on_site"},
    "dispatched": {"en_route", "on_site"},
    "en_route": {"on_site"},
    "on_site": {"in_progress"},
    "in_progress": {"paused", "completed", "follow_up_required"},
    "paused": {"in_progress", "follow_up_required"},
    "follow_up_required": {"in_progress"},
}


@dataclass(slots=True)
class JobService:
    db: Session
    context: SecurityContext

    def _require_staff(self) -> None:
        if not self.context.is_staff:
            raise PermissionError("Scheduling and dispatch are restricted to NTInet staff.")

    def ntinet_organization(self) -> Organization:
        self._require_staff()
        organization = self.db.scalar(select(Organization).where(
            Organization.slug == "ntinet", Organization.organization_type == Organization.STAFF_TYPE,
            Organization.active.is_(True)))
        if organization is None:
            raise ValueError("The NTInet staff organization is not configured.")
        return organization

    def scope(self, statement: Select) -> Select:
        self._require_staff()
        organization = self.ntinet_organization()
        statement = statement.where(Job.owning_organization_id == organization.id)
        if not self.context.can("jobs.dispatch"):
            statement = statement.where(or_(
                Job.primary_technician_id == self.context.user_id,
                Job.assignments.any(JobAssignment.user_id == self.context.user_id),
            ))
        return statement

    def list(self, *, query: str = "", status: str = "", priority: str = "",
             technician_id: int | None = None, customer_id: int | None = None,
             limit: int = 500) -> list[Job]:
        statement = self.scope(select(Job))
        if query.strip():
            term = f"%{query.strip().lower()}%"
            statement = statement.join(Customer, Job.customer_id == Customer.id).where(or_(
                func.lower(Job.job_number).like(term), func.lower(Job.summary).like(term),
                func.lower(Customer.name).like(term)))
        if status in JOB_STATUSES: statement = statement.where(Job.status == status)
        if priority in JOB_PRIORITIES: statement = statement.where(Job.priority == priority)
        if technician_id: statement = statement.where(or_(Job.primary_technician_id == technician_id,
            Job.assignments.any(JobAssignment.user_id == technician_id)))
        if customer_id: statement = statement.where(Job.customer_id == customer_id)
        return list(self.db.scalars(statement.order_by(Job.updated_at.desc()).limit(max(1, min(limit, 2000)))).unique())

    def get(self, job_id: int) -> Job | None:
        return self.db.scalar(self.scope(select(Job).where(Job.id == job_id)))

    def my_work(self, limit: int = 100) -> list[Job]:
        statement = self.scope(select(Job)).where(Job.status.not_in({"completed", "cancelled"}))
        return list(self.db.scalars(statement.order_by(
            Job.scheduled_start.asc().nulls_last(), Job.priority.desc(), Job.created_at
        ).limit(max(1, min(limit, 500)))).unique())

    def customers(self) -> list[Customer]:
        self._require_staff()
        return CustomerService(self.db, self.context).list(status="active", limit=2000)

    def technicians(self) -> list[User]:
        organization = self.ntinet_organization()
        return list(self.db.scalars(select(User).where(
            User.organization_id == organization.id, User.active.is_(True), User.deleted_at.is_(None)
        ).order_by(User.full_name)).unique())

    def _validate_customer(self, customer_id: int, contact_id: int | None,
                           location_id: int, ticket_id: int | None) -> tuple[Customer, Ticket | None]:
        customer = CustomerService(self.db, self.context).get(customer_id)
        if customer is None: raise ValueError("Customer not found.")
        if contact_id and contact_id not in {item.id for item in customer.contacts}:
            raise ValueError("The selected contact does not belong to this customer.")
        location = self.db.scalar(select(CustomerLocation).where(
            CustomerLocation.id == location_id, CustomerLocation.customer_id == customer.id,
            CustomerLocation.active.is_(True)))
        if location is None: raise ValueError("An active service location belonging to the customer is required.")
        ticket = None
        if ticket_id:
            ticket = self.db.scalar(select(Ticket).where(Ticket.id == ticket_id, Ticket.customer_id == customer.id))
            if ticket is None: raise ValueError("The selected ticket does not belong to this customer.")
        return customer, ticket

    def _validate_schedule(self, start: datetime | None, end: datetime | None,
                           duration: int) -> tuple[datetime | None, datetime | None, int]:
        duration = max(15, min(int(duration), 1440))
        if end and not start: raise ValueError("A scheduled start is required when an end time is supplied.")
        if start and not end: end = start + timedelta(minutes=duration)
        if start and end and end <= start: raise ValueError("Scheduled end must be after scheduled start.")
        if start and end: duration = max(15, int((end - start).total_seconds() // 60))
        return start, end, duration

    def _set_assignments(self, job: Job, primary_id: int | None, crew_ids: list[int], actor_id: int) -> None:
        valid = {user.id for user in self.technicians()}
        selected = list(dict.fromkeys(([primary_id] if primary_id else []) + crew_ids))
        if any(user_id not in valid for user_id in selected): raise ValueError("A selected technician is not an active NTInet user.")
        job.assignments.clear(); self.db.flush()
        for user_id in selected:
            job.assignments.append(JobAssignment(user_id=user_id, is_primary=user_id == primary_id,
                                                 assigned_by_user_id=actor_id))
        job.primary_technician_id = primary_id

    def create(self, *, customer_id: int, contact_id: int | None, location_id: int,
               ticket_id: int | None, job_type: str, priority: str, summary: str,
               description: str, internal_instructions: str, customer_notes: str,
               scheduled_start: datetime | None, scheduled_end: datetime | None,
               estimated_duration_minutes: int, primary_technician_id: int | None,
               crew_ids: list[int]) -> Job:
        self._require_staff(); customer, ticket = self._validate_customer(customer_id, contact_id, location_id, ticket_id)
        if job_type not in JOB_TYPES or priority not in JOB_PRIORITIES: raise ValueError("Invalid job type or priority.")
        if not summary.strip() or not description.strip(): raise ValueError("Job summary and description are required.")
        start, end, duration = self._validate_schedule(scheduled_start, scheduled_end, estimated_duration_minutes)
        organization = self.ntinet_organization()
        job = Job(job_number=f"PENDING-{self.context.user_id}-{int(datetime.now(timezone.utc).timestamp())}",
            owning_organization_id=organization.id, customer_id=customer.id, contact_id=contact_id,
            location_id=location_id, ticket_id=ticket.id if ticket else None, job_type=job_type,
            priority=priority, status="scheduled" if start else "unscheduled", summary=summary.strip(),
            description=description.strip(), internal_instructions=internal_instructions.strip(),
            customer_notes=customer_notes.strip(), scheduled_start=start, scheduled_end=end,
            estimated_duration_minutes=duration, created_by_user_id=self.context.user_id,
            updated_by_user_id=self.context.user_id)
        self.db.add(job); self.db.flush(); job.job_number = f"JOB-{job.id:06d}"
        self._set_assignments(job, primary_technician_id, crew_ids, self.context.user_id)
        self.activity(job, "created", f"Job created for {customer.name}.")
        if start:
            from app.services.job_communication_service import JobCommunicationService
            JobCommunicationService(self.db).schedule_changed(
                job,rescheduled=False,actor_user_id=self.context.user_id)
        if ticket:
            from app.database.ticket_models import TicketEntry
            visibility = "customer" if ticket.source == "third_party_portal" else "internal"
            self.db.add(TicketEntry(ticket_id=ticket.id, entry_type="system", visibility=visibility,
                                    body=f"Field service job {job.job_number} created: {job.summary}",
                                    author_user_id=self.context.user_id))
        return job

    def update(self, job: Job, *, job_type: str, priority: str, status: str, summary: str,
               description: str, internal_instructions: str, customer_notes: str,
               completion_summary: str, scheduled_start: datetime | None, scheduled_end: datetime | None,
               estimated_duration_minutes: int, primary_technician_id: int | None,
               crew_ids: list[int]) -> Job:
        if job_type not in JOB_TYPES or priority not in JOB_PRIORITIES or status not in JOB_STATUSES:
            raise ValueError("Invalid job type, priority, or status.")
        if not summary.strip() or not description.strip(): raise ValueError("Job summary and description are required.")
        start, end, duration = self._validate_schedule(scheduled_start, scheduled_end, estimated_duration_minutes)
        old_status = job.status
        job.job_type=job_type; job.priority=priority; job.status=status; job.summary=summary.strip()
        job.description=description.strip(); job.internal_instructions=internal_instructions.strip()
        job.customer_notes=customer_notes.strip(); job.completion_summary=completion_summary.strip()
        job.scheduled_start=start; job.scheduled_end=end; job.estimated_duration_minutes=duration
        job.updated_by_user_id=self.context.user_id
        self._set_assignments(job, primary_technician_id, crew_ids, self.context.user_id)
        now = datetime.now(timezone.utc)
        timestamp_fields = {"dispatched":"dispatched_at", "en_route":"en_route_at", "on_site":"arrived_at",
                            "in_progress":"started_at", "completed":"completed_at", "cancelled":"cancelled_at"}
        if status in timestamp_fields and getattr(job, timestamp_fields[status]) is None:
            setattr(job, timestamp_fields[status], now)
        if old_status != status: self.activity(job, "status_changed", f"Status changed from {old_status.replace('_',' ').title()} to {status.replace('_',' ').title()}.")
        else: self.activity(job, "updated", "Job details updated.")
        if old_status != "cancelled" and status == "cancelled":
            from app.services.job_communication_service import JobCommunicationService
            JobCommunicationService(self.db).appointment_cancelled(job,actor_user_id=self.context.user_id)
        return job

    def schedule(self, job: Job, *, scheduled_start: datetime | None,
                 scheduled_end: datetime | None, estimated_duration_minutes: int,
                 primary_technician_id: int | None, crew_ids: list[int]) -> Job:
        start, end, duration = self._validate_schedule(
            scheduled_start, scheduled_end, estimated_duration_minutes)
        old_start, old_end, old_primary = job.scheduled_start, job.scheduled_end, job.primary_technician_id
        job.scheduled_start = start
        job.scheduled_end = end
        job.estimated_duration_minutes = duration
        job.updated_by_user_id = self.context.user_id
        self._set_assignments(job, primary_technician_id, crew_ids, self.context.user_id)
        if start and job.status == "unscheduled":
            job.status = "scheduled"
        elif not start and job.status == "scheduled":
            job.status = "unscheduled"
        if start:
            detail = f"Scheduled for {start.strftime('%m/%d/%Y %I:%M %p')} for approximately {duration} minutes."
        else:
            detail = "Job schedule cleared and returned to the unscheduled queue."
        schedule_changed = old_start != start or old_end != end
        customer_schedule_changed = old_start != start
        if schedule_changed or old_primary != primary_technician_id:
            self.activity(job, "schedule_updated", detail)
        if customer_schedule_changed:
            from app.services.job_communication_service import JobCommunicationService
            communications=JobCommunicationService(self.db)
            if start:
                communications.schedule_changed(job,rescheduled=old_start is not None,
                                                actor_user_id=self.context.user_id)
            elif old_start:
                communications.appointment_cancelled(job,actor_user_id=self.context.user_id)
        return job

    def board_jobs(self, start: datetime, end: datetime) -> list[Job]:
        statement = self.scope(select(Job)).where(
            Job.scheduled_start.is_not(None),
            Job.scheduled_start < end,
            or_(Job.scheduled_end.is_(None), Job.scheduled_end > start),
            Job.status != "cancelled",
        )
        return list(self.db.scalars(statement.order_by(Job.scheduled_start, Job.priority.desc())).unique())

    def unscheduled_jobs(self, limit: int = 250) -> list[Job]:
        statement = self.scope(select(Job)).where(
            or_(Job.scheduled_start.is_(None), Job.status == "unscheduled"),
            Job.status.not_in({"completed", "cancelled"}),
        )
        return list(self.db.scalars(statement.order_by(Job.priority.desc(), Job.created_at).limit(limit)).unique())

    def scheduling_conflicts(self, technician_id: int, start: datetime, end: datetime,
                             exclude_job_id: int | None = None) -> list[Job]:
        statement = self.scope(select(Job)).where(
            Job.id != (exclude_job_id or -1),
            Job.status.not_in({"completed", "cancelled"}),
            Job.scheduled_start.is_not(None),
            Job.scheduled_start < end,
            or_(Job.scheduled_end.is_(None), Job.scheduled_end > start),
            or_(Job.primary_technician_id == technician_id,
                Job.assignments.any(JobAssignment.user_id == technician_id)),
        )
        return list(self.db.scalars(statement.order_by(Job.scheduled_start)).unique())

    def dispatch_move(self, job: Job, *, technician_id: int | None,
                      scheduled_start: datetime, allow_conflict: bool = False) -> list[Job]:
        duration = max(15, int(job.estimated_duration_minutes or 60))
        scheduled_end = scheduled_start + timedelta(minutes=duration)
        conflicts = self.scheduling_conflicts(
            technician_id, scheduled_start, scheduled_end, job.id) if technician_id else []
        if conflicts and not allow_conflict:
            return conflicts
        crew_ids = [assignment.user_id for assignment in job.assignments
                    if not assignment.is_primary and assignment.user_id != technician_id]
        old_technician = job.primary_technician.full_name if job.primary_technician else "Unassigned"
        self.schedule(job, scheduled_start=scheduled_start, scheduled_end=scheduled_end,
                      estimated_duration_minutes=duration,
                      primary_technician_id=technician_id, crew_ids=crew_ids)
        new_technician = next((user.full_name for user in self.technicians()
                               if user.id == technician_id), "Unassigned")
        self.activity(job, "dispatch_board_move",
                      f"Moved on dispatch board from {old_technician} to {new_technician} at "
                      f"{scheduled_start.strftime('%m/%d/%Y %I:%M %p')}.")
        return conflicts

    def technician_update(self, job: Job, *, status: str | None, note: str = "",
                          completion_summary: str = "") -> Job:
        note = note.strip()
        completion_summary = completion_summary.strip()
        if status is None:
            if not note: raise ValueError("Enter a technician note before saving.")
            self.activity(job, "technician_note", note)
            job.updated_by_user_id = self.context.user_id
            return job
        allowed = TECHNICIAN_TRANSITIONS.get(job.status, set())
        if status not in allowed:
            raise ValueError(
                f"A {job.status.replace('_', ' ')} job cannot be changed to "
                f"{status.replace('_', ' ')} from the technician workflow."
            )
        if status == "completed" and not completion_summary:
            raise ValueError("A completion summary is required before completing the job.")
        if status in {"paused", "follow_up_required"} and not note:
            raise ValueError("Add a note explaining why the job is paused or needs follow-up.")
        previous = job.status
        job.status = status
        job.updated_by_user_id = self.context.user_id
        now = datetime.now(timezone.utc)
        timestamp_fields = {
            "en_route": "en_route_at", "on_site": "arrived_at",
            "in_progress": "started_at", "completed": "completed_at",
        }
        field = timestamp_fields.get(status)
        if field and getattr(job, field) is None: setattr(job, field, now)
        if status == "completed": job.completion_summary = completion_summary
        detail = f"Status changed from {previous.replace('_', ' ').title()} to {status.replace('_', ' ').title()}."
        if note: detail += f" {note}"
        if completion_summary: detail += f" Completion: {completion_summary}"
        self.activity(job, "technician_status", detail)
        if status == "en_route":
            from app.services.job_communication_service import JobCommunicationService
            JobCommunicationService(self.db).technician_en_route(
                job,actor_user_id=self.context.user_id)
        if job.ticket and status in {"completed", "follow_up_required"}:
            from app.database.ticket_models import TicketEntry
            ticket_detail = (f"{job.job_number} marked {status.replace('_', ' ')} by field technician. "
                             f"{completion_summary or note}").strip()
            visibility = "customer" if job.ticket.source == "third_party_portal" else "internal"
            self.db.add(TicketEntry(ticket_id=job.ticket.id, entry_type="system", visibility=visibility,
                                    body=ticket_detail, author_user_id=self.context.user_id))
        return job

    def activity(self, job: Job, activity_type: str, detail: str, visibility: str = "internal") -> JobActivity:
        record = JobActivity(job_id=job.id, activity_type=activity_type, visibility=visibility,
                             detail=detail.strip(), actor_user_id=self.context.user_id)
        self.db.add(record); return record
