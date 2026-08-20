"""TKT-4D scheduling communications.

Revision ID: 20260806_12
Revises: 20260806_11
"""
from alembic import op
import sqlalchemy as sa

revision = "20260806_12"
down_revision = "20260806_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_communication_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_communication_id", sa.Integer(), sa.ForeignKey("customer_communications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("deduplication_key", sa.String(length=160), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("deduplication_key", name="uq_job_comm_dedupe"),
    )
    for name, column in (
        ("ix_job_comm_job", "job_id"), ("ix_job_comm_customer_msg", "customer_communication_id"),
        ("ix_job_comm_event", "event_type"), ("ix_job_comm_channel", "channel"),
        ("ix_job_comm_status", "status"), ("ix_job_comm_dedupe", "deduplication_key"),
        ("ix_job_comm_scheduled", "scheduled_for"), ("ix_job_comm_created", "created_at"),
    ):
        op.create_index(name, "job_communication_events", [column])


def downgrade() -> None:
    op.drop_table("job_communication_events")
