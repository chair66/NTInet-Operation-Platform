"""TKT-3A outbound ticket communications.

Revision ID: 20260806_04
Revises: 20260806_03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260806_04"
down_revision: Union[str, None] = "20260806_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "ticket_outbound_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=True),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_message_id", sa.String(160), nullable=False),
        sa.Column("deduplication_key", sa.String(180), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entry_id"], ["ticket_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    for column in ("ticket_id","entry_id","contact_id","channel","destination","event_type","status","provider_message_id","next_attempt_at","created_at"):
        op.create_index(f"ix_ticket_outbound_messages_{column}", "ticket_outbound_messages", [column])
    op.create_index("ix_ticket_outbound_messages_deduplication_key", "ticket_outbound_messages", ["deduplication_key"], unique=True)

def downgrade() -> None:
    op.drop_table("ticket_outbound_messages")
