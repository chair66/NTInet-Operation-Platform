"""TKT-3B customer communications inbox.

Revision ID: 20260806_06
Revises: 20260806_05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_06"
down_revision: Union[str, None] = "20260806_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_communications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("communication_profile_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source_address", sa.String(255), nullable=False),
        sa.Column("destination_address", sa.String(255), nullable=False),
        sa.Column("profile_name", sa.String(120), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_message_id", sa.String(160), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("consent_override", sa.Boolean(), nullable=False),
        sa.Column("consent_override_reason", sa.Text(), nullable=False),
        sa.Column("thread_key", sa.String(180), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["communication_profile_id"], ["communication_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    for column in ("customer_id", "contact_id", "ticket_id", "organization_id",
                   "communication_profile_id", "direction", "channel", "source_address",
                   "destination_address", "provider_message_id", "status", "thread_key", "created_at"):
        op.create_index(f"ix_customer_communications_{column}", "customer_communications", [column])


def downgrade() -> None:
    op.drop_table("customer_communications")
