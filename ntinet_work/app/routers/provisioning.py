from fastapi import APIRouter, Request
from sqlalchemy import select
from app.database import SessionLocal
from app.database.models import ProvisioningJob, ProvisioningTemplate
from app.security import require_permission
from app.web import render

router = APIRouter(prefix="/provisioning", tags=["Provisioning"])


@router.get("")
def provisioning_home(request: Request):
    require_permission(request, "provisioning.read")
    with SessionLocal() as db:
        jobs = list(db.scalars(select(ProvisioningJob).order_by(ProvisioningJob.created_at.desc()).limit(10)))
        for job in jobs:
            _ = job.organization.name if job.organization else None
            db.expunge(job)
    return render(request, "provisioning/index.html", jobs=jobs)


@router.get("/jobs")
def provisioning_jobs(request: Request):
    require_permission(request, "provisioning.read")
    with SessionLocal() as db:
        jobs = list(db.scalars(select(ProvisioningJob).order_by(ProvisioningJob.created_at.desc()).limit(100)))
        for job in jobs:
            _ = job.organization.name if job.organization else None
            db.expunge(job)
    return render(request, "provisioning/jobs.html", jobs=jobs)


@router.get("/templates")
def provisioning_templates(request: Request):
    require_permission(request, "provisioning.read")
    with SessionLocal() as db:
        templates = list(db.scalars(select(ProvisioningTemplate).order_by(ProvisioningTemplate.name)))
        for template in templates:
            db.expunge(template)
    return render(request, "provisioning/templates.html", templates=templates)
