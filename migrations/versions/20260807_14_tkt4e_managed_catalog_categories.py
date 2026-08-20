"""TKT-4E managed catalog categories.

Revision ID: 20260807_14
Revises: 20260807_13
"""
from alembic import op
import sqlalchemy as sa

revision = "20260807_14"
down_revision = "20260807_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "name", name="uq_catalog_category_org_name"),
    )
    op.create_index("ix_cat_category_org", "catalog_categories", ["organization_id"])
    op.create_index("ix_cat_category_name", "catalog_categories", ["name"])
    op.create_index("ix_cat_category_active", "catalog_categories", ["active"])
    op.add_column("catalog_items", sa.Column("category_id", sa.Integer(), nullable=True))

    # Preserve every existing category while collapsing case-only variations.
    op.execute(sa.text("""
        INSERT INTO catalog_categories (organization_id, name, description, active, created_at, updated_at)
        SELECT organization_id, display_name, '', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM (
            SELECT DISTINCT ON (organization_id, LOWER(COALESCE(NULLIF(BTRIM(category), ''), 'Uncategorized')))
                organization_id,
                COALESCE(NULLIF(BTRIM(category), ''), 'Uncategorized') AS display_name
            FROM catalog_items
            ORDER BY organization_id, LOWER(COALESCE(NULLIF(BTRIM(category), ''), 'Uncategorized')), id
        ) existing_categories
    """))
    op.execute(sa.text("""
        UPDATE catalog_items AS item
        SET category_id = category.id,
            category = category.name
        FROM catalog_categories AS category
        WHERE category.organization_id = item.organization_id
          AND LOWER(category.name) = LOWER(COALESCE(NULLIF(BTRIM(item.category), ''), 'Uncategorized'))
    """))
    op.alter_column("catalog_items", "category_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_catalog_item_category", "catalog_items", "catalog_categories", ["category_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_catalog_category_id", "catalog_items", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_catalog_category_id", table_name="catalog_items")
    op.drop_constraint("fk_catalog_item_category", "catalog_items", type_="foreignkey")
    op.drop_column("catalog_items", "category_id")
    op.drop_table("catalog_categories")
