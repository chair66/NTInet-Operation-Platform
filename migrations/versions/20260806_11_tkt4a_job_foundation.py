"""TKT-4A job foundation.

Revision ID: 20260806_11
Revises: 20260806_10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_11"
down_revision: Union[str, None] = "20260806_10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_number", sa.String(32), nullable=False),
        sa.Column("owning_organization_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("primary_technician_id", sa.Integer(), nullable=True),
        sa.Column("job_type", sa.String(40), nullable=False, server_default="service_call"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(30), nullable=False, server_default="unscheduled"),
        sa.Column("summary", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("internal_instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column("customer_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("completion_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("en_route_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owning_organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["customer_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["primary_technician_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("job_number", name="uq_jobs_job_number"),
    )
    for column, name in {
        "job_number":"ix_jobs_job_number", "owning_organization_id":"ix_jobs_owner",
        "customer_id":"ix_jobs_customer", "contact_id":"ix_jobs_contact",
        "location_id":"ix_jobs_location", "ticket_id":"ix_jobs_ticket",
        "primary_technician_id":"ix_jobs_primary_tech", "job_type":"ix_jobs_type",
        "priority":"ix_jobs_priority", "status":"ix_jobs_status",
        "summary":"ix_jobs_summary", "scheduled_start":"ix_jobs_scheduled_start",
        "scheduled_end":"ix_jobs_scheduled_end", "created_at":"ix_jobs_created_at",
        "updated_at":"ix_jobs_updated_at",
    }.items(): op.create_index(name, "jobs", [column])

    op.create_table(
        "job_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("job_id", "user_id", name="uq_job_assignment_user"),
    )
    op.create_index("ix_job_assignments_job", "job_assignments", ["job_id"])
    op.create_index("ix_job_assignments_user", "job_assignments", ["user_id"])

    op.create_table(
        "job_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="internal"),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    for column, name in {"job_id":"ix_job_activities_job", "activity_type":"ix_job_activities_type",
                         "visibility":"ix_job_activities_visibility", "actor_user_id":"ix_job_activities_actor",
                         "created_at":"ix_job_activities_created_at"}.items():
        op.create_index(name, "job_activities", [column])


def downgrade() -> None:
    op.drop_table("job_activities")
    op.drop_table("job_assignments")
    op.drop_table("jobs")
