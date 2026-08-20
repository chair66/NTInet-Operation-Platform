"""TKT-4F.1 online acceptance, estimate reply links, and user signatures."""
from alembic import op
import sqlalchemy as sa

revision="20260807_17"
down_revision="20260807_16"
branch_labels=None
depends_on=None


def upgrade() -> None:
    op.add_column("estimates",sa.Column("won_option_ids_json",sa.Text(),nullable=False,server_default="[]"))
    op.add_column("estimates",sa.Column("accepted_by_name",sa.String(160),nullable=False,server_default=""))
    op.add_column("estimates",sa.Column("accepted_by_email",sa.String(255),nullable=False,server_default=""))
    op.add_column("estimates",sa.Column("accepted_signature_data",sa.Text(),nullable=False,server_default=""))
    op.add_column("estimates",sa.Column("accepted_ip_address",sa.String(64),nullable=False,server_default=""))
    op.add_column("estimates",sa.Column("accepted_at",sa.DateTime(timezone=True),nullable=True))
    op.execute(sa.text("UPDATE estimates SET status='won' WHERE status='accepted'"))
    op.execute(sa.text("UPDATE estimates e SET won_option_ids_json=(SELECT COALESCE('['||string_agg(id::text,',')||']','[]') FROM estimate_options WHERE estimate_id=e.id) WHERE e.status='won'"))
    op.add_column("estimate_deliveries",sa.Column("acceptance_token",sa.String(1000),nullable=False,server_default=""))
    op.add_column("customer_communications",sa.Column("estimate_id",sa.Integer(),nullable=True))
    op.create_foreign_key("fk_customer_communications_estimate","customer_communications","estimates",["estimate_id"],["id"],ondelete="SET NULL")
    op.create_index("ix_customer_communications_estimate_id","customer_communications",["estimate_id"])
    op.add_column("communication_conversations",sa.Column("estimate_id",sa.Integer(),nullable=True))
    op.create_foreign_key("fk_communication_conversations_estimate","communication_conversations","estimates",["estimate_id"],["id"],ondelete="SET NULL")
    op.create_index("ix_communication_conversations_estimate_id","communication_conversations",["estimate_id"])
    op.add_column("users",sa.Column("email_signature",sa.Text(),nullable=False,server_default=""))
    op.add_column("users",sa.Column("signature_photo_filename",sa.String(255),nullable=False,server_default=""))
    op.add_column("users",sa.Column("signature_photo_content_type",sa.String(100),nullable=False,server_default=""))


def downgrade() -> None:
    op.drop_column("users","signature_photo_content_type")
    op.drop_column("users","signature_photo_filename")
    op.drop_column("users","email_signature")
    op.drop_index("ix_communication_conversations_estimate_id",table_name="communication_conversations")
    op.drop_constraint("fk_communication_conversations_estimate","communication_conversations",type_="foreignkey")
    op.drop_column("communication_conversations","estimate_id")
    op.drop_index("ix_customer_communications_estimate_id",table_name="customer_communications")
    op.drop_constraint("fk_customer_communications_estimate","customer_communications",type_="foreignkey")
    op.drop_column("customer_communications","estimate_id")
    op.drop_column("estimate_deliveries","acceptance_token")
    for column in ("accepted_at","accepted_ip_address","accepted_signature_data","accepted_by_email","accepted_by_name","won_option_ids_json"):
        op.drop_column("estimates",column)
