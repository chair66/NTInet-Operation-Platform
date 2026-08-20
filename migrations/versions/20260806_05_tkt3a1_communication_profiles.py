"""TKT-3A.1 multi-organization communication profiles.

Revision ID: 20260806_05
Revises: 20260806_04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "20260806_05"
down_revision: Union[str, None] = "20260806_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("communication_profiles",
        sa.Column("id",sa.Integer(),primary_key=True), sa.Column("organization_id",sa.Integer(),nullable=False),
        sa.Column("module_slug",sa.String(80),nullable=False), sa.Column("channel",sa.String(20),nullable=False),
        sa.Column("provider",sa.String(40),nullable=False), sa.Column("name",sa.String(120),nullable=False),
        sa.Column("from_name",sa.String(120),nullable=False), sa.Column("sender_address",sa.String(255),nullable=False),
        sa.Column("reply_to",sa.String(255),nullable=False), sa.Column("smtp_host",sa.String(255),nullable=False),
        sa.Column("smtp_port",sa.Integer(),nullable=False), sa.Column("smtp_username",sa.String(255),nullable=False),
        sa.Column("smtp_password_encrypted",sa.Text(),nullable=False), sa.Column("smtp_security",sa.String(20),nullable=False),
        sa.Column("bandwidth_account_id",sa.String(80),nullable=False), sa.Column("bandwidth_username",sa.String(255),nullable=False),
        sa.Column("bandwidth_password_encrypted",sa.Text(),nullable=False), sa.Column("bandwidth_application_id",sa.String(120),nullable=False),
        sa.Column("bandwidth_campaign_id",sa.String(120),nullable=False), sa.Column("bandwidth_api_base",sa.String(255),nullable=False),
        sa.Column("is_default",sa.Boolean(),nullable=False), sa.Column("is_active",sa.Boolean(),nullable=False),
        sa.Column("is_shareable",sa.Boolean(),nullable=False), sa.Column("daily_limit",sa.Integer(),nullable=False),
        sa.Column("last_test_status",sa.String(20),nullable=False), sa.Column("last_test_message",sa.Text(),nullable=False),
        sa.Column("last_tested_at",sa.DateTime(timezone=True),nullable=True), sa.Column("created_by_user_id",sa.Integer(),nullable=True),
        sa.Column("updated_by_user_id",sa.Integer(),nullable=True), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["organization_id"],["organizations.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"],["users.id"],ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"],["users.id"],ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id","channel","name",name="uq_communication_profile_org_channel_name"))
    for c in ("organization_id","module_slug","channel","provider","is_default","is_active","is_shareable","created_at"):
        op.create_index(f"ix_communication_profiles_{c}","communication_profiles",[c])
    op.add_column("tickets",sa.Column("email_profile_id",sa.Integer(),nullable=True))
    op.add_column("tickets",sa.Column("sms_profile_id",sa.Integer(),nullable=True))
    op.create_foreign_key("fk_tickets_email_profile","tickets","communication_profiles",["email_profile_id"],["id"],ondelete="SET NULL")
    op.create_foreign_key("fk_tickets_sms_profile","tickets","communication_profiles",["sms_profile_id"],["id"],ondelete="SET NULL")
    op.create_index("ix_tickets_email_profile_id","tickets",["email_profile_id"])
    op.create_index("ix_tickets_sms_profile_id","tickets",["sms_profile_id"])
    op.add_column("ticket_outbound_messages",sa.Column("communication_profile_id",sa.Integer(),nullable=True))
    op.add_column("ticket_outbound_messages",sa.Column("profile_name",sa.String(120),nullable=False,server_default=""))
    op.add_column("ticket_outbound_messages",sa.Column("sender_identity",sa.String(255),nullable=False,server_default=""))
    op.create_foreign_key("fk_outbound_communication_profile","ticket_outbound_messages","communication_profiles",["communication_profile_id"],["id"],ondelete="SET NULL")
    op.create_index("ix_ticket_outbound_messages_communication_profile_id","ticket_outbound_messages",["communication_profile_id"])

def downgrade() -> None:
    op.drop_index("ix_ticket_outbound_messages_communication_profile_id", table_name="ticket_outbound_messages")
    op.drop_constraint("fk_outbound_communication_profile", "ticket_outbound_messages", type_="foreignkey")
    op.drop_column("ticket_outbound_messages","sender_identity"); op.drop_column("ticket_outbound_messages","profile_name")
    op.drop_column("ticket_outbound_messages","communication_profile_id")
    op.drop_index("ix_tickets_sms_profile_id", table_name="tickets")
    op.drop_index("ix_tickets_email_profile_id", table_name="tickets")
    op.drop_constraint("fk_tickets_sms_profile", "tickets", type_="foreignkey")
    op.drop_constraint("fk_tickets_email_profile", "tickets", type_="foreignkey")
    op.drop_column("tickets","sms_profile_id"); op.drop_column("tickets","email_profile_id")
    op.drop_table("communication_profiles")
