from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import ProvisioningJob, ProvisioningTask


class ProvisioningEngine:
    """Synchronous Sprint 1 job framework; provider execution arrives in Sprint 2."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(self, *, name: str, organization_id: int | None, created_by: int | None,
                   template_key: str = "manual") -> ProvisioningJob:
        job = ProvisioningJob(
            name=name,
            organization_id=organization_id,
            created_by=created_by,
            template_key=template_key,
            status="pending",
        )
        self.db.add(job)
        self.db.flush()
        return job

    def add_task(self, job: ProvisioningJob, *, sequence: int, name: str,
                 provider_slug: str | None = None, action: str = "noop") -> ProvisioningTask:
        task = ProvisioningTask(
            job_id=job.id,
            sequence=sequence,
            name=name,
            provider_slug=provider_slug,
            action=action,
            status="pending",
        )
        self.db.add(task)
        self.db.flush()
        return task

    def mark_running(self, job: ProvisioningJob) -> None:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)

    def mark_completed(self, job: ProvisioningJob) -> None:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)

    def tasks_for(self, job_id: int) -> list[ProvisioningTask]:
        return list(self.db.scalars(
            select(ProvisioningTask)
            .where(ProvisioningTask.job_id == job_id)
            .order_by(ProvisioningTask.sequence)
        ))
