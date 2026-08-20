"""TKT-4E sub-categories and vendor item details.

Revision ID: 20260807_15
Revises: 20260807_14
"""
from alembic import op
import sqlalchemy as sa

revision = "20260807_15"
down_revision = "20260807_14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalog_categories", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_catalog_category_parent", "catalog_categories", "catalog_categories", ["parent_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_cat_category_parent", "catalog_categories", ["parent_id"])
    op.add_column("catalog_items", sa.Column("brand", sa.String(120), nullable=False, server_default=""))
    op.add_column("catalog_items", sa.Column("model_number", sa.String(120), nullable=False, server_default=""))
    op.add_column("catalog_items", sa.Column("ordering_note", sa.Text(), nullable=False, server_default=""))
    op.add_column("catalog_items", sa.Column("ordering_url", sa.String(1000), nullable=False, server_default=""))
    op.create_index("ix_catalog_brand", "catalog_items", ["brand"])
    op.create_index("ix_catalog_model", "catalog_items", ["model_number"])


def downgrade() -> None:
    op.drop_index("ix_catalog_model", table_name="catalog_items")
    op.drop_index("ix_catalog_brand", table_name="catalog_items")
    op.drop_column("catalog_items", "ordering_url")
    op.drop_column("catalog_items", "ordering_note")
    op.drop_column("catalog_items", "model_number")
    op.drop_column("catalog_items", "brand")
    op.drop_index("ix_cat_category_parent", table_name="catalog_categories")
    op.drop_constraint("fk_catalog_category_parent", "catalog_categories", type_="foreignkey")
    op.drop_column("catalog_categories", "parent_id")
