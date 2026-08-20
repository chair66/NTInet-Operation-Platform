"""SMS OAuth authentication hotfix.

Revision ID: 20260806_07
Revises: 20260806_06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260806_07"
down_revision: Union[str, None] = "20260806_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("communication_profiles", sa.Column("bandwidth_auth_mode", sa.String(30), nullable=False, server_default="oauth2_system"))
    op.add_column("communication_profiles", sa.Column("bandwidth_client_id", sa.String(255), nullable=False, server_default=""))
    op.add_column("communication_profiles", sa.Column("bandwidth_client_secret_encrypted", sa.Text(), nullable=False, server_default=""))
    op.add_column("communication_profiles", sa.Column("bandwidth_token_url", sa.String(255), nullable=False, server_default="https://api.bandwidth.com/api/v1/oauth2/token"))


def downgrade() -> None:
    op.drop_column("communication_profiles", "bandwidth_token_url")
    op.drop_column("communication_profiles", "bandwidth_client_secret_encrypted")
    op.drop_column("communication_profiles", "bandwidth_client_id")
    op.drop_column("communication_profiles", "bandwidth_auth_mode")
