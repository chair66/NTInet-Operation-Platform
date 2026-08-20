"""TKT-3C.1 GreenGeeks inbound email and notifications.

Revision ID: 20260806_10
Revises: 20260806_09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_10"
down_revision: Union[str, None] = "20260806_09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("communication_profiles") as batch:
        batch.add_column(sa.Column("inbound_email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("imap_host", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("imap_port", sa.Integer(), nullable=False, server_default="993"))
        batch.add_column(sa.Column("imap_username", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("imap_password_encrypted", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("imap_security", sa.String(20), nullable=False, server_default="ssl"))
        batch.add_column(sa.Column("imap_folder", sa.String(120), nullable=False, server_default="INBOX"))
        batch.add_column(sa.Column("imap_uidvalidity", sa.String(80), nullable=False, server_default=""))
        batch.add_column(sa.Column("imap_last_uid", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("imap_last_sync_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("imap_last_sync_status", sa.String(30), nullable=False, server_default="not_synced"))
        batch.add_column(sa.Column("imap_last_sync_message", sa.Text(), nullable=False, server_default=""))
        batch.create_index("ix_comm_profile_inbound_email", ["inbound_email_enabled"])

    with op.batch_alter_table("notification_events") as batch:
        batch.add_column(sa.Column("target_url", sa.String(500), nullable=False, server_default=""))
        batch.add_column(sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_notification_events_read_at", ["read_at"])

    op.create_table(
        "inbound_email_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("communication_profile_id", sa.Integer(), nullable=False),
        sa.Column("uidvalidity", sa.String(80), nullable=False, server_default=""),
        sa.Column("imap_uid", sa.Integer(), nullable=False),
        sa.Column("email_message_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("sender_address", sa.String(255), nullable=False, server_default=""),
        sa.Column("subject", sa.String(255), nullable=False, server_default=""),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="received"),
        sa.Column("customer_communication_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["communication_profile_id"], ["communication_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_communication_id"], ["customer_communications.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("communication_profile_id", "uidvalidity", "imap_uid", name="uq_inbound_email_profile_uid"),
    )
    indexes = {
        "communication_profile_id": "ix_inbound_email_profile",
        "email_message_id": "ix_inbound_email_message_id",
        "sender_address": "ix_inbound_email_sender",
        "processing_status": "ix_inbound_email_status",
        "customer_communication_id": "ix_inbound_email_customer_comm",
        "created_at": "ix_inbound_email_created_at",
    }
    for column, name in indexes.items():
        op.create_index(name, "inbound_email_imports", [column])


def downgrade() -> None:
    op.drop_table("inbound_email_imports")
    with op.batch_alter_table("notification_events") as batch:
        batch.drop_index("ix_notification_events_read_at")
        batch.drop_column("read_at")
        batch.drop_column("target_url")
    with op.batch_alter_table("communication_profiles") as batch:
        batch.drop_index("ix_comm_profile_inbound_email")
        for column in ("imap_last_sync_message", "imap_last_sync_status", "imap_last_sync_at",
                       "imap_last_uid", "imap_uidvalidity", "imap_folder", "imap_security",
                       "imap_password_encrypted", "imap_username", "imap_port", "imap_host",
                       "inbound_email_enabled"):
            batch.drop_column(column)
