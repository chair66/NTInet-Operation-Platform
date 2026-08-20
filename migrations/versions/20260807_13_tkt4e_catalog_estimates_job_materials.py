"""TKT-4E products services estimates and job materials.

Revision ID: 20260807_13
Revises: 20260806_12
"""
from alembic import op
import sqlalchemy as sa

revision = "20260807_13"
down_revision = "20260806_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("catalog_items",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("organization_id",sa.Integer(),sa.ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False),
        sa.Column("sku",sa.String(60),nullable=False),sa.Column("item_type",sa.String(20),nullable=False),
        sa.Column("category",sa.String(100),nullable=False,server_default=""),sa.Column("name",sa.String(180),nullable=False),
        sa.Column("description",sa.Text(),nullable=False,server_default=""),sa.Column("unit",sa.String(30),nullable=False,server_default="each"),
        sa.Column("unit_cost",sa.Numeric(14,4),nullable=False,server_default="0"),sa.Column("unit_price",sa.Numeric(14,4),nullable=False,server_default="0"),
        sa.Column("taxable",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("created_by_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("updated_by_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint("organization_id","sku",name="uq_catalog_org_sku"))
    for name,column in (("ix_catalog_org","organization_id"),("ix_catalog_sku","sku"),("ix_catalog_type","item_type"),("ix_catalog_category","category"),("ix_catalog_name","name"),("ix_catalog_taxable","taxable"),("ix_catalog_active","active"),("ix_catalog_created","created_at")): op.create_index(name,"catalog_items",[column])

    op.create_table("estimates",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("estimate_number",sa.String(32),nullable=False),
        sa.Column("organization_id",sa.Integer(),sa.ForeignKey("organizations.id"),nullable=False),
        sa.Column("customer_id",sa.Integer(),sa.ForeignKey("customers.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("contact_id",sa.Integer(),sa.ForeignKey("customer_contacts.id",ondelete="SET NULL"),nullable=True),
        sa.Column("location_id",sa.Integer(),sa.ForeignKey("customer_locations.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("job_id",sa.Integer(),sa.ForeignKey("jobs.id",ondelete="SET NULL"),nullable=True),
        sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("title",sa.String(200),nullable=False),
        sa.Column("internal_notes",sa.Text(),nullable=False,server_default=""),sa.Column("customer_notes",sa.Text(),nullable=False,server_default=""),
        sa.Column("valid_until",sa.Date(),nullable=True),sa.Column("tax_rate",sa.Numeric(8,4),nullable=False,server_default="0"),
        sa.Column("subtotal",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("discount_total",sa.Numeric(14,2),nullable=False,server_default="0"),
        sa.Column("taxable_subtotal",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("tax_total",sa.Numeric(14,2),nullable=False,server_default="0"),
        sa.Column("total",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("estimated_cost",sa.Numeric(14,2),nullable=False,server_default="0"),
        sa.Column("gross_profit",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("margin_percent",sa.Numeric(8,2),nullable=False,server_default="0"),
        sa.Column("created_by_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("updated_by_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint("estimate_number",name="uq_estimate_number"))
    for name,column in (("ix_est_number","estimate_number"),("ix_est_org","organization_id"),("ix_est_customer","customer_id"),("ix_est_contact","contact_id"),("ix_est_location","location_id"),("ix_est_job","job_id"),("ix_est_status","status"),("ix_est_created","created_at")): op.create_index(name,"estimates",[column])

    op.create_table("estimate_line_items",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("estimate_id",sa.Integer(),sa.ForeignKey("estimates.id",ondelete="CASCADE"),nullable=False),
        sa.Column("catalog_item_id",sa.Integer(),sa.ForeignKey("catalog_items.id",ondelete="SET NULL"),nullable=True),sa.Column("sort_order",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("item_type",sa.String(20),nullable=False),sa.Column("sku",sa.String(60),nullable=False,server_default=""),sa.Column("description",sa.String(500),nullable=False),sa.Column("unit",sa.String(30),nullable=False,server_default="each"),
        sa.Column("quantity",sa.Numeric(14,3),nullable=False,server_default="1"),sa.Column("unit_cost",sa.Numeric(14,4),nullable=False,server_default="0"),sa.Column("unit_price",sa.Numeric(14,4),nullable=False,server_default="0"),
        sa.Column("discount_percent",sa.Numeric(8,3),nullable=False,server_default="0"),sa.Column("taxable",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("line_cost",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("line_subtotal",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("line_discount",sa.Numeric(14,2),nullable=False,server_default="0"),sa.Column("line_total",sa.Numeric(14,2),nullable=False,server_default="0"))
    op.create_index("ix_est_line_estimate","estimate_line_items",["estimate_id"]); op.create_index("ix_est_line_catalog","estimate_line_items",["catalog_item_id"])

    op.create_table("job_line_items",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("job_id",sa.Integer(),sa.ForeignKey("jobs.id",ondelete="CASCADE"),nullable=False),
        sa.Column("catalog_item_id",sa.Integer(),sa.ForeignKey("catalog_items.id",ondelete="SET NULL"),nullable=True),
        sa.Column("estimate_line_item_id",sa.Integer(),sa.ForeignKey("estimate_line_items.id",ondelete="SET NULL"),nullable=True),sa.Column("sort_order",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("item_type",sa.String(20),nullable=False),sa.Column("sku",sa.String(60),nullable=False,server_default=""),sa.Column("description",sa.String(500),nullable=False),sa.Column("unit",sa.String(30),nullable=False,server_default="each"),
        sa.Column("estimated_quantity",sa.Numeric(14,3),nullable=False,server_default="0"),sa.Column("actual_quantity",sa.Numeric(14,3),nullable=False,server_default="0"),
        sa.Column("estimated_unit_cost",sa.Numeric(14,4),nullable=False,server_default="0"),sa.Column("actual_unit_cost",sa.Numeric(14,4),nullable=False,server_default="0"),sa.Column("unit_price",sa.Numeric(14,4),nullable=False,server_default="0"),
        sa.Column("discount_percent",sa.Numeric(8,3),nullable=False,server_default="0"),sa.Column("taxable",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("billable",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("created_by_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),sa.Column("updated_by_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_job_line_job","job_line_items",["job_id"]); op.create_index("ix_job_line_catalog","job_line_items",["catalog_item_id"]); op.create_index("ix_job_line_estimate","job_line_items",["estimate_line_item_id"])


def downgrade() -> None:
    op.drop_table("job_line_items"); op.drop_table("estimate_line_items"); op.drop_table("estimates"); op.drop_table("catalog_items")
