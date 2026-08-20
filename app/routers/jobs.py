from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import func, select

from app.database import SessionLocal
from app.database.customer_models import CustomerLocation
from app.database.job_models import Job
from app.config import get_settings
from app.database.ticket_models import Ticket
from app.security import context_from_request, require_permission
from app.services import AuditService, CustomerCommunicationService, JobService
from app.services.job_service import JOB_PRIORITIES, JOB_STATUSES, JOB_TYPES, TECHNICIAN_TRANSITIONS
from app.web import render, templates

router = APIRouter(prefix="/jobs", tags=["Scheduling and Dispatch"])

STATUS_LABELS = {value: value.replace("_", " ").title() for value in JOB_STATUSES}
TYPE_LABELS = {value: value.replace("_", " ").title() for value in JOB_TYPES}
PRIORITY_LABELS = {value: value.title() for value in JOB_PRIORITIES}
settings = get_settings()


def staff_context(request: Request):
    context = context_from_request(request)
    if not context.is_staff: raise HTTPException(403, "Scheduling and dispatch are restricted to NTInet staff.")
    return context


def parse_int(value: str | int | None) -> int | None:
    if value is None or not str(value).strip(): return None
    try: return int(value)
    except (TypeError, ValueError) as exc: raise HTTPException(400, "Invalid selection") from exc


def application_zone(timezone_name: str | None = None) -> ZoneInfo:
    try: return ZoneInfo(timezone_name or settings.app_timezone)
    except ZoneInfoNotFoundError: return ZoneInfo(settings.app_timezone)


def parse_datetime(value: str, timezone_name: str | None = None) -> datetime | None:
    if not value.strip(): return None
    try: parsed = datetime.fromisoformat(value.strip())
    except ValueError as exc: raise HTTPException(400, "Invalid schedule date/time") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=application_zone(timezone_name))
    return parsed.astimezone(timezone.utc)


def redirect_job(job_id: int, message: str = ""):
    suffix = f"?message={quote(message)}" if message else ""
    return RedirectResponse(f"/jobs/{job_id}{suffix}", status_code=303)


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def local(value: datetime, timezone_name: str | None = None) -> datetime:
    return aware(value).astimezone(application_zone(timezone_name))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def job_list(request: Request, q: str = "", status: str = "", priority: str = "",
             technician_id: str = "", customer_id: str = ""):
    require_permission(request, "jobs.read"); context = staff_context(request)
    with SessionLocal() as db:
        service = JobService(db, context)
        jobs = service.list(query=q, status=status, priority=priority,
                            technician_id=parse_int(technician_id), customer_id=parse_int(customer_id))
        all_jobs = service.list(limit=2000)
        technicians = service.technicians(); customers = service.customers()
        metrics = {"total":len(all_jobs), "unscheduled":sum(j.status == "unscheduled" for j in all_jobs),
                   "scheduled":sum(j.status in {"scheduled","dispatched","en_route","on_site","in_progress"} for j in all_jobs),
                   "completed":sum(j.status == "completed" for j in all_jobs)}
        db.expunge_all()
    return render(request, "jobs/list.html", jobs=jobs, technicians=technicians, customers=customers,
                  metrics=metrics, filters={"q":q,"status":status,"priority":priority,
                  "technician_id":parse_int(technician_id),"customer_id":parse_int(customer_id)},
                  status_labels=STATUS_LABELS, priority_labels=PRIORITY_LABELS)


@router.get("/new", response_class=HTMLResponse)
def job_new(request: Request, ticket_id: int | None = None, customer_id: int | None = None):
    require_permission(request, "jobs.create"); context = staff_context(request)
    with SessionLocal() as db:
        service=JobService(db,context); customers=service.customers(); technicians=service.technicians(); ticket=None
        if ticket_id:
            ticket=db.scalar(select(Ticket).where(Ticket.id==ticket_id)); customer_id=ticket.customer_id if ticket else customer_id
        for customer in customers: _=tuple(customer.contacts); _=tuple(customer.locations)
        db.expunge_all()
    return render(request,"jobs/form.html",job=None,customers=customers,technicians=technicians,
                  selected_customer_id=customer_id,selected_ticket=ticket,status_labels=STATUS_LABELS,
                  priority_labels=PRIORITY_LABELS,type_labels=TYPE_LABELS)


@router.post("")
def job_create(request: Request, customer_id:int=Form(...), location_id:int=Form(...),
               contact_id:str=Form(""), ticket_id:str=Form(""), job_type:str=Form("service_call"),
               priority:str=Form("normal"), summary:str=Form(...), description:str=Form(...),
               internal_instructions:str=Form(""), customer_notes:str=Form(""),
               scheduled_start:str=Form(""), scheduled_end:str=Form(""),
               estimated_duration_minutes:int=Form(60), primary_technician_id:str=Form(""),
               crew_ids:list[str]=Form([])):
    require_permission(request,"jobs.create"); context=staff_context(request)
    with SessionLocal() as db:
        try:
            location=db.scalar(select(CustomerLocation).where(CustomerLocation.id==location_id))
            location_timezone=location.timezone if location else settings.app_timezone
            job=JobService(db,context).create(customer_id=customer_id,contact_id=parse_int(contact_id),
                location_id=location_id,ticket_id=parse_int(ticket_id),job_type=job_type,priority=priority,
                summary=summary,description=description,internal_instructions=internal_instructions,
                customer_notes=customer_notes,scheduled_start=parse_datetime(scheduled_start,location_timezone),
                scheduled_end=parse_datetime(scheduled_end,location_timezone),estimated_duration_minutes=estimated_duration_minutes,
                primary_technician_id=parse_int(primary_technician_id),crew_ids=[int(v) for v in crew_ids if v])
            AuditService(db,request,context).record("jobs.created","job",job.id,f"Created {job.job_number}: {job.summary}",
                module="field-service",organization_id=job.owning_organization_id); db.commit(); job_id=job.id
        except (ValueError,PermissionError) as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect_job(job_id,"Job created.")


@router.get("/dispatch", response_class=HTMLResponse)
def dispatch_board(request:Request,board_date:str="",view:str="day",technician_id:str=""):
    require_permission(request,"jobs.dispatch"); context=staff_context(request)
    try: selected=date.fromisoformat(board_date) if board_date else datetime.now().date()
    except ValueError: raise HTTPException(400,"Invalid dispatch board date")
    view="week" if view=="week" else "day"; selected_technician=parse_int(technician_id)
    period_start=selected-timedelta(days=selected.weekday()) if view=="week" else selected
    day_count=7 if view=="week" else 1
    board_zone=application_zone()
    start=datetime.combine(period_start,time.min,tzinfo=board_zone).astimezone(timezone.utc)
    end=(datetime.combine(period_start,time.min,tzinfo=board_zone)+timedelta(days=day_count)).astimezone(timezone.utc)
    with SessionLocal() as db:
        service=JobService(db,context); all_technicians=service.technicians(); technicians=all_technicians
        if selected_technician: technicians=[item for item in all_technicians if item.id==selected_technician]
        jobs=service.board_jobs(start,end); unscheduled=service.unscheduled_jobs()
        if selected_technician:
            jobs=[job for job in jobs if job.primary_technician_id==selected_technician or
                  any(a.user_id==selected_technician for a in job.assignments)]
        if view=="day":
            work_start=7; work_end=20; lane_width=(work_end-work_start)*100
            lanes=[{"id":None,"name":"Unassigned","jobs":[]}]+[
                {"id":tech.id,"name":tech.full_name,"jobs":[]} for tech in technicians]
            lane_by_id={lane["id"]:lane for lane in lanes}
            for job in jobs:
                start_value=local(job.scheduled_start); end_value=local(job.scheduled_end) if job.scheduled_end else start_value+timedelta(minutes=job.estimated_duration_minutes)
                minutes=(start_value-datetime.combine(selected,time(work_start),tzinfo=board_zone)).total_seconds()/60
                duration=max(15,(end_value-start_value).total_seconds()/60)
                item={"job":job,"left":max(0,minutes/60*100),"width":max(58,min(duration/60*100,lane_width-max(0,minutes/60*100))),
                      "starts_before":minutes<0,"ends_after":minutes+duration>(work_end-work_start)*60}
                lane_by_id.get(job.primary_technician_id,lane_by_id[None])["jobs"].append(item)
            week_days=[]
        else:
            week_days=[period_start+timedelta(days=index) for index in range(7)]
            lanes=[{"id":None,"name":"Unassigned","days":{day:[] for day in week_days}}]+[
                {"id":tech.id,"name":tech.full_name,"days":{day:[] for day in week_days}} for tech in technicians]
            lane_by_id={lane["id"]:lane for lane in lanes}
            for job in jobs:
                job_day=local(job.scheduled_start).date()
                if job_day in lane_by_id.get(job.primary_technician_id,lane_by_id[None])["days"]:
                    lane_by_id.get(job.primary_technician_id,lane_by_id[None])["days"][job_day].append(job)
            work_start=7; work_end=20; lane_width=1300
        for job in jobs: _=tuple(job.assignments)
        db.expunge_all()
    previous=period_start-timedelta(days=7 if view=="week" else 1)
    following=period_start+timedelta(days=7 if view=="week" else 1)
    return render(request,"jobs/dispatch.html",lanes=lanes,unscheduled=unscheduled,
                  technicians=technicians,all_technicians=all_technicians,selected_date=selected,period_start=period_start,
                  week_days=week_days,view=view,work_start=work_start,work_end=work_end,
                  lane_width=lane_width,previous_date=previous,following_date=following,
                  selected_technician_id=selected_technician)


@router.post("/{job_id}/dispatch-move")
async def dispatch_move(request:Request,job_id:int):
    require_permission(request,"jobs.dispatch"); context=staff_context(request)
    try: payload=await request.json()
    except Exception as exc: raise HTTPException(400,"Invalid dispatch update") from exc
    technician_id=parse_int(payload.get("technician_id"))
    try: scheduled_start=parse_datetime(str(payload.get("scheduled_start") or ""))
    except HTTPException: raise
    if scheduled_start is None: raise HTTPException(400,"A schedule time is required")
    with SessionLocal() as db:
        service=JobService(db,context); job=service.get(job_id)
        if not job: raise HTTPException(404,"Job not found")
        try:
            conflicts=service.dispatch_move(job,technician_id=technician_id,
                scheduled_start=scheduled_start,allow_conflict=bool(payload.get("allow_conflict")))
            if conflicts and not payload.get("allow_conflict"):
                return JSONResponse({"detail":"This technician already has overlapping work.",
                    "conflicts":[{"job_number":item.job_number,"summary":item.summary,
                    "start":aware(item.scheduled_start).isoformat()} for item in conflicts]},status_code=409)
            AuditService(db,request,context).record("jobs.dispatch_board_move","job",job.id,
                f"Moved {job.job_number} on dispatch board",module="field-service",
                organization_id=job.owning_organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return {"ok":True,"job_id":job_id,"scheduled_start":scheduled_start.isoformat()}


@router.get("/my-work", response_class=HTMLResponse)
def my_work(request:Request):
    require_permission(request,"jobs.read"); context=staff_context(request)
    with SessionLocal() as db:
        service=JobService(db,context); jobs=service.my_work()
        today=datetime.now(application_zone()).date()
        active_statuses={"en_route","on_site","in_progress","paused","follow_up_required"}
        active=[job for job in jobs if job.status in active_statuses]
        today_jobs=[job for job in jobs if job.status not in active_statuses and job.scheduled_start
                    and local(job.scheduled_start).date()==today]
        upcoming=[job for job in jobs if job not in active and job not in today_jobs]
        for job in jobs: _=tuple(job.assignments); _=tuple(job.activities)
        db.expunge_all()
    return render(request,"jobs/my_work.html",active_jobs=active,today_jobs=today_jobs,
                  upcoming_jobs=upcoming,today=today,status_labels=STATUS_LABELS,
                  transition_map=TECHNICIAN_TRANSITIONS,message=request.query_params.get("message",""))


@router.get("/{job_id}", response_class=HTMLResponse)
def job_detail(request:Request,job_id:int,message:str=""):
    require_permission(request,"jobs.read"); context=staff_context(request)
    with SessionLocal() as db:
        service=JobService(db,context); job=service.get(job_id)
        if not job: raise HTTPException(404,"Job not found")
        technicians=service.technicians(); _=tuple(job.assignments); _=tuple(job.activities); _=tuple(job.line_items)
        from app.services.catalog_service import CatalogService
        catalog_service=CatalogService(db,context)
        catalog=catalog_service.catalog() if context.can("catalog.read") else []
        job_financials=catalog_service.job_financials(job)
        # Hide legacy internal SKU identifiers from job users.
        for item in catalog: item.sku=""
        for line in job.line_items:
            line.sku=""
            line.estimated_quantity=f"{line.estimated_quantity:.1f}" if line.item_type=="labor" else f"{line.estimated_quantity:.0f}"
            line.actual_quantity=f"{line.actual_quantity:.1f}" if line.item_type=="labor" else f"{line.actual_quantity:.0f}"
        contacts=[contact for contact in job.customer.contacts if contact.active and contact.email]
        db.expunge_all()
    return render(request,"jobs/detail.html",job=job,technicians=technicians,message=message,
                  status_labels=STATUS_LABELS,priority_labels=PRIORITY_LABELS,type_labels=TYPE_LABELS,
                  catalog=catalog,job_financials=job_financials,contacts=contacts)


@router.get("/{job_id}/print",response_class=HTMLResponse)
def job_print(request:Request,job_id:int):
    require_permission(request,"jobs.read"); context=staff_context(request)
    with SessionLocal() as db:
        job=JobService(db,context).get(job_id)
        if not job: raise HTTPException(404,"Job not found")
        _=tuple(job.line_items); _=tuple(job.assignments)
        for line in job.line_items:
            line.estimated_quantity=f"{line.estimated_quantity:.1f}" if line.item_type=="labor" else f"{line.estimated_quantity:.0f}"
            line.actual_quantity=f"{line.actual_quantity:.1f}" if line.item_type=="labor" else f"{line.actual_quantity:.0f}"
        db.expunge_all()
    return render(request,"documents/job_print.html",job=job)


@router.post("/{job_id}/email")
def job_email(request:Request,job_id:int,contact_id:int=Form(...)):
    require_permission(request,"jobs.manage"); context=staff_context(request)
    with SessionLocal() as db:
        job=JobService(db,context).get(job_id)
        if not job: raise HTTPException(404,"Job not found")
        _=tuple(job.line_items)
        html=templates.env.get_template("documents/job_email.html").render(job=job)
        try:
            record=CustomerCommunicationService(db).send(job.customer,contact_id=contact_id,channel="email",subject=f"Work Order {job.job_number} from NTInet",body=f"Work order {job.job_number}: {job.summary}",profile_id=None,ticket_id=job.ticket_id,consent_override=False,override_reason="",actor_user_id=context.user_id,module_slug="field-service",html_body=html)
            AuditService(db,request,context).record("jobs.emailed","job",job.id,f"Work order email {record.status} to {record.destination_address}",module="field-service",organization_id=job.owning_organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    message="Work order emailed successfully." if record.status=="sent" else f"Work order email {record.status}: {record.error_message}"
    return redirect_job(job_id,message)


@router.post("/{job_id}/update")
def job_update(request:Request,job_id:int,job_type:str=Form(...),priority:str=Form(...),status:str=Form(...),
               summary:str=Form(...),description:str=Form(...),internal_instructions:str=Form(""),
               customer_notes:str=Form(""),completion_summary:str=Form("")):
    require_permission(request,"jobs.manage"); context=staff_context(request)
    with SessionLocal() as db:
        service=JobService(db,context); job=service.get(job_id)
        if not job: raise HTTPException(404,"Job not found")
        try:
            service.update(job,job_type=job_type,priority=priority,status=status,summary=summary,
                description=description,internal_instructions=internal_instructions,customer_notes=customer_notes,
                completion_summary=completion_summary,scheduled_start=job.scheduled_start,
                scheduled_end=job.scheduled_end,estimated_duration_minutes=job.estimated_duration_minutes,
                primary_technician_id=job.primary_technician_id,
                crew_ids=[item.user_id for item in job.assignments if not item.is_primary])
            AuditService(db,request,context).record("jobs.updated","job",job.id,f"Updated {job.job_number}",
                module="field-service",organization_id=job.owning_organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect_job(job_id,"Job updated.")


@router.post("/{job_id}/status")
def technician_status(request:Request,job_id:int,status:str=Form(...),note:str=Form("")):
    context=staff_context(request)
    if not context.can("jobs.manage"): raise HTTPException(403,"Job management permission required")
    with SessionLocal() as db:
        service=JobService(db,context); job=service.get(job_id)
        if not job: raise HTTPException(404,"Job not found or not assigned to you")
        if status not in JOB_STATUSES: raise HTTPException(400,"Invalid job status")
        old=job.status; job.status=status; job.updated_by_user_id=context.user_id
        now=datetime.now(timezone.utc); fields={"dispatched":"dispatched_at","en_route":"en_route_at","on_site":"arrived_at","in_progress":"started_at","completed":"completed_at","cancelled":"cancelled_at"}
        if status in fields and getattr(job,fields[status]) is None: setattr(job,fields[status],now)
        service.activity(job,"status_changed",f"Status changed from {old.replace('_',' ').title()} to {status.replace('_',' ').title()}." + (f" {note.strip()}" if note.strip() else ""))
        if old!="cancelled" and status=="cancelled":
            from app.services.job_communication_service import JobCommunicationService
            JobCommunicationService(db).appointment_cancelled(job,actor_user_id=context.user_id)
        db.commit()
    return redirect_job(job_id,"Job status updated.")


@router.post("/{job_id}/technician-update")
def technician_workflow_update(request:Request,job_id:int,status:str=Form(""),note:str=Form(""),
                               completion_summary:str=Form(""),return_to:str=Form("job")):
    context=staff_context(request)
    if not (context.can("jobs.manage") or context.can("jobs.technician")):
        raise HTTPException(403,"Technician workflow permission required")
    with SessionLocal() as db:
        service=JobService(db,context); job=service.get(job_id)
        if not job: raise HTTPException(404,"Job not found or not assigned to you")
        try:
            service.technician_update(job,status=status or None,note=note,
                                      completion_summary=completion_summary)
            AuditService(db,request,context).record("jobs.technician_workflow","job",job.id,
                f"Technician workflow update for {job.job_number}",module="field-service",
                organization_id=job.owning_organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    if return_to=="my-work":
        return RedirectResponse("/jobs/my-work?message="+quote("Work order updated."),status_code=303)
    return redirect_job(job_id,"Work order updated.")


@router.post("/{job_id}/schedule")
def job_schedule(request:Request,job_id:int,scheduled_start:str=Form(""),scheduled_end:str=Form(""),
                 estimated_duration_minutes:int=Form(60),primary_technician_id:str=Form(""),
                 crew_ids:list[str]=Form([])):
    context=staff_context(request)
    if not (context.can("jobs.dispatch") or context.can("jobs.manage")):
        raise HTTPException(403,"Dispatch permission required")
    with SessionLocal() as db:
        service=JobService(db,context); job=service.get(job_id)
        if not job: raise HTTPException(404,"Job not found")
        try:
            service.schedule(job,scheduled_start=parse_datetime(scheduled_start,job.location.timezone),
                scheduled_end=parse_datetime(scheduled_end,job.location.timezone),estimated_duration_minutes=estimated_duration_minutes,
                primary_technician_id=parse_int(primary_technician_id),
                crew_ids=[int(value) for value in crew_ids if value])
            AuditService(db,request,context).record("jobs.schedule_updated","job",job.id,
                f"Updated schedule for {job.job_number}",module="field-service",
                organization_id=job.owning_organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect_job(job_id,"Job schedule updated.")
