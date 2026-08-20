"""DigiCloud organization billing ownership.

Revision ID: 20260818_01
Revises: 20260807_18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260818_01"
down_revision: Union[str, None] = "20260807_18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("digicloud_organization_settings", sa.Column("billing_model", sa.String(20), nullable=False, server_default="direct"))
    op.add_column("digicloud_organization_settings", sa.Column("platypus_parent_customer_id", sa.String(40), nullable=False, server_default=""))
    op.add_column("digicloud_organization_settings", sa.Column("wholesale_rate_group_ids", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("digicloud_organization_settings", sa.Column("default_wholesale_rate_group_id", sa.String(20), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("digicloud_organization_settings", "default_wholesale_rate_group_id")
    op.drop_column("digicloud_organization_settings", "wholesale_rate_group_ids")
    op.drop_column("digicloud_organization_settings", "platypus_parent_customer_id")
    op.drop_column("digicloud_organization_settings", "billing_model")
