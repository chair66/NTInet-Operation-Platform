"""TKT-3B.1 Bandwidth Messaging production webhooks.

Revision ID: 20260806_08
Revises: 20260806_07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_08"
down_revision: Union[str, None] = "20260806_07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customer_communications", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customer_communications", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customer_communications", sa.Column("provider_error_code", sa.String(40), nullable=False, server_default=""))
    op.add_column("customer_communications", sa.Column("delivery_description", sa.Text(), nullable=False, server_default=""))
    op.create_table(
        "bandwidth_messaging_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deduplication_key", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("provider_message_id", sa.String(160), nullable=False, server_default=""),
        sa.Column("application_id", sa.String(120), nullable=False, server_default=""),
        sa.Column("source_address", sa.String(40), nullable=False, server_default=""),
        sa.Column("destination_address", sa.String(40), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("error_code", sa.String(40), nullable=False, server_default=""),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="received"),
        sa.Column("customer_communication_id", sa.Integer(), nullable=True),
        sa.Column("ticket_outbound_message_id", sa.Integer(), nullable=True),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_communication_id"], ["customer_communications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_outbound_message_id"], ["ticket_outbound_messages.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("deduplication_key", name="uq_bandwidth_webhook_deduplication_key"),
    )
    indexes = {
        "deduplication_key": "ix_bw_msg_webhook_dedupe",
        "event_type": "ix_bw_msg_webhook_event_type",
        "provider_message_id": "ix_bw_msg_webhook_message_id",
        "application_id": "ix_bw_msg_webhook_application_id",
        "source_address": "ix_bw_msg_webhook_source",
        "destination_address": "ix_bw_msg_webhook_destination",
        "processing_status": "ix_bw_msg_webhook_status",
        "customer_communication_id": "ix_bw_msg_webhook_customer_comm",
        "ticket_outbound_message_id": "ix_bw_msg_webhook_ticket_message",
        "created_at": "ix_bw_msg_webhook_created_at",
    }
    for column, index_name in indexes.items():
        op.create_index(index_name, "bandwidth_messaging_webhook_events", [column])


def downgrade() -> None:
    op.drop_table("bandwidth_messaging_webhook_events")
    op.drop_column("customer_communications", "delivery_description")
    op.drop_column("customer_communications", "provider_error_code")
    op.drop_column("customer_communications", "failed_at")
    op.drop_column("customer_communications", "delivered_at")
