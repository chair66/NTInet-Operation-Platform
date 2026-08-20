"""TKT-2 core support tickets.

Revision ID: 20260806_03
Revises: 20260806_02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260806_03"
down_revision: Union[str, None] = "20260806_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_number", sa.String(32), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("owning_organization_id", sa.Integer(), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ticket_type", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_target_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["customer_locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["service_id"], ["customer_services.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owning_organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    for column in (
        "ticket_number", "customer_id", "contact_id", "location_id", "service_id",
        "owning_organization_id", "assigned_user_id", "subject", "ticket_type",
        "priority", "status", "source", "sla_target_at", "created_at", "updated_at",
    ):
        op.create_index(
            f"ix_tickets_{column}", "tickets", [column], unique=column == "ticket_number"
        )

    op.create_table(
        "ticket_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(30), nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    for column in ("ticket_id", "entry_type", "visibility", "author_user_id", "created_at"):
        op.create_index(f"ix_ticket_entries_{column}", "ticket_entries", [column])

    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entry_id"], ["ticket_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("stored_filename", name="uq_ticket_attachment_stored_filename"),
    )
    for column in ("ticket_id", "entry_id", "created_at"):
        op.create_index(f"ix_ticket_attachments_{column}", "ticket_attachments", [column])


def downgrade() -> None:
    op.drop_table("ticket_attachments")
    op.drop_table("ticket_entries")
    op.drop_table("tickets")
