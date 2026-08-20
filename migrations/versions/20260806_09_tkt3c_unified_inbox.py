"""TKT-3C unified communications inbox and conversation threads.

Revision ID: 20260806_09
Revises: 20260806_08
"""
from typing import Sequence, Union
import hashlib
import re

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_09"
down_revision: Union[str, None] = "20260806_08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "communication_conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("communication_profile_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False, server_default=""),
        sa.Column("thread_key", sa.String(180), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_message_preview", sa.String(255), nullable=False, server_default=""),
        sa.Column("last_direction", sa.String(20), nullable=False, server_default=""),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["communication_profile_id"], ["communication_profiles.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("thread_key", name="uq_communication_conversation_thread_key"),
    )
    indexes = {
        "organization_id": "ix_comm_conversation_org",
        "customer_id": "ix_comm_conversation_customer",
        "contact_id": "ix_comm_conversation_contact",
        "ticket_id": "ix_comm_conversation_ticket",
        "assigned_user_id": "ix_comm_conversation_assignee",
        "communication_profile_id": "ix_comm_conversation_profile",
        "channel": "ix_comm_conversation_channel",
        "thread_key": "ix_comm_conversation_thread_key",
        "status": "ix_comm_conversation_status",
        "unread_count": "ix_comm_conversation_unread",
        "last_direction": "ix_comm_conversation_direction",
        "last_message_at": "ix_comm_conversation_last_message",
        "created_at": "ix_comm_conversation_created_at",
    }
    for column, name in indexes.items():
        op.create_index(name, "communication_conversations", [column])

    with op.batch_alter_table("customer_communications") as batch:
        batch.add_column(sa.Column("conversation_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("email_message_id", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("email_in_reply_to", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("email_references", sa.Text(), nullable=False, server_default=""))
        batch.create_foreign_key("fk_customer_communications_conversation", "communication_conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_customer_communications_conversation_id", ["conversation_id"])
        batch.create_index("ix_customer_communications_is_read", ["is_read"])
        batch.create_index("ix_customer_communications_email_message_id", ["email_message_id"])
        batch.create_index("ix_customer_communications_email_in_reply_to", ["email_in_reply_to"])

    bind = op.get_bind()
    rows = bind.execute(sa.text("""
        SELECT id, customer_id, contact_id, ticket_id, organization_id,
               communication_profile_id, channel, subject, body, direction,
               thread_key, created_at
        FROM customer_communications ORDER BY created_at, id
    """)).mappings().all()
    conversations: dict[str, int] = {}
    for row in rows:
        if row["channel"] == "email" and row["subject"]:
            normalized_subject = re.sub(r"^\s*((re|fw|fwd)\s*:\s*)+", "", row["subject"], flags=re.I).strip().lower()
            subject_hash = hashlib.sha256(normalized_subject.encode()).hexdigest()[:20]
            key = f"customer-{row['customer_id']}:email:{row['contact_id'] or 0}:{subject_hash}"
        else:
            key = (row["thread_key"] or f"legacy:{row['customer_id']}:{row['channel']}:{row['contact_id'] or 0}")[:180]
        conversation_id = conversations.get(key)
        if conversation_id is None:
            conversation_id = bind.execute(sa.text("""
                INSERT INTO communication_conversations
                    (organization_id, customer_id, contact_id, ticket_id,
                     communication_profile_id, channel, subject, thread_key,
                     status, unread_count, last_message_preview, last_direction,
                     last_message_at, created_at, updated_at)
                VALUES
                    (:organization_id, :customer_id, :contact_id, :ticket_id,
                     :profile_id, :channel, :subject, :thread_key,
                     'open', :unread_count, :preview, :direction,
                     :message_at, :message_at, :message_at)
                RETURNING id
            """), {
                "organization_id": row["organization_id"], "customer_id": row["customer_id"],
                "contact_id": row["contact_id"], "ticket_id": row["ticket_id"],
                "profile_id": row["communication_profile_id"], "channel": row["channel"],
                "subject": row["subject"] or "", "thread_key": key,
                "unread_count": 1 if row["direction"] == "inbound" else 0,
                "preview": (row["body"] or "")[:255], "direction": row["direction"],
                "message_at": row["created_at"],
            }).scalar_one()
            conversations[key] = conversation_id
        else:
            bind.execute(sa.text("""
                UPDATE communication_conversations SET
                    ticket_id = COALESCE(:ticket_id, ticket_id),
                    communication_profile_id = COALESCE(:profile_id, communication_profile_id),
                    last_message_preview = :preview, last_direction = :direction,
                    last_message_at = :message_at, updated_at = :message_at,
                    unread_count = unread_count + :unread_increment
                WHERE id = :conversation_id
            """), {
                "ticket_id": row["ticket_id"], "profile_id": row["communication_profile_id"],
                "preview": (row["body"] or "")[:255], "direction": row["direction"],
                "message_at": row["created_at"], "unread_increment": 1 if row["direction"] == "inbound" else 0,
                "conversation_id": conversation_id,
            })
        bind.execute(sa.text("""
            UPDATE customer_communications SET conversation_id=:conversation_id,
                is_read=:is_read, read_at=CASE WHEN :is_read THEN created_at ELSE NULL END
            WHERE id=:message_id
        """), {"conversation_id": conversation_id, "is_read": row["direction"] != "inbound", "message_id": row["id"]})


def downgrade() -> None:
    with op.batch_alter_table("customer_communications") as batch:
        batch.drop_index("ix_customer_communications_email_in_reply_to")
        batch.drop_index("ix_customer_communications_email_message_id")
        batch.drop_index("ix_customer_communications_is_read")
        batch.drop_index("ix_customer_communications_conversation_id")
        batch.drop_constraint("fk_customer_communications_conversation", type_="foreignkey")
        for column in ("email_references", "email_in_reply_to", "email_message_id", "read_at", "is_read", "conversation_id"):
            batch.drop_column(column)
    op.drop_table("communication_conversations")
