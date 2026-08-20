from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.core import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    owning_organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("customer_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("customer_locations.id", ondelete="RESTRICT"), index=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    primary_technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    job_type: Mapped[str] = mapped_column(String(40), default="service_call", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", index=True)
    status: Mapped[str] = mapped_column(String(30), default="unscheduled", index=True)
    summary: Mapped[str] = mapped_column(String(240), index=True)
    description: Mapped[str] = mapped_column(Text)
    internal_instructions: Mapped[str] = mapped_column(Text, default="")
    customer_notes: Mapped[str] = mapped_column(Text, default="")
    completion_summary: Mapped[str] = mapped_column(Text, default="")
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    en_route_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, index=True)

    owning_organization = relationship("Organization", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    contact = relationship("CustomerContact", lazy="joined")
    location = relationship("CustomerLocation", lazy="joined")
    ticket = relationship("Ticket", back_populates="jobs", lazy="joined")
    primary_technician = relationship("User", foreign_keys=[primary_technician_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_user_id], lazy="joined")
    assignments: Mapped[list["JobAssignment"]] = relationship(back_populates="job", cascade="all, delete-orphan", lazy="selectin")
    activities: Mapped[list["JobActivity"]] = relationship(back_populates="job", cascade="all, delete-orphan", lazy="selectin", order_by="JobActivity.created_at")
    communication_events: Mapped[list["JobCommunicationEvent"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", lazy="selectin",
        order_by="JobCommunicationEvent.created_at")
    line_items = relationship("JobLineItem", back_populates="job", cascade="all, delete-orphan",
                              lazy="selectin", order_by="JobLineItem.sort_order")
    estimates = relationship("Estimate", back_populates="job", lazy="selectin")


class JobAssignment(Base):
    __tablename__ = "job_assignments"
    __table_args__ = (UniqueConstraint("job_id", "user_id", name="uq_job_assignment_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    assigned_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    job = relationship("Job", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id], lazy="joined")


class JobActivity(Base):
    __tablename__ = "job_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    activity_type: Mapped[str] = mapped_column(String(40), index=True)
    visibility: Mapped[str] = mapped_column(String(20), default="internal", index=True)
    detail: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    job = relationship("Job", back_populates="activities")
    actor = relationship("User", lazy="joined")


class JobCommunicationEvent(Base):
    __tablename__ = "job_communication_events"
    __table_args__ = (UniqueConstraint("deduplication_key", name="uq_job_comm_dedupe"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    customer_communication_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_communications.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    deduplication_key: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    job = relationship("Job", back_populates="communication_events", lazy="select")
    customer_communication = relationship("CustomerCommunication", lazy="select")
    created_by = relationship("User", lazy="select")
