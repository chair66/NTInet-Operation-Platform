"""Initial PostgreSQL schema for the existing NOP application."""

from pathlib import Path
from typing import Sequence, Union

from alembic import op


revision: str = "20260806_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _schema_statements() -> list[str]:
    schema_path = Path(__file__).resolve().parents[1] / "schema_v1.sql"
    sql = schema_path.read_text(encoding="utf-8")
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def upgrade() -> None:
    for statement in _schema_statements():
        op.execute(statement)


def downgrade() -> None:
    # CASCADE is intentional here: downgrading the initial revision is a
    # destructive removal of the entire NOP schema.
    tables = [
        "mobile_port_requests", "mobile_lines", "mobile_exceptions",
        "mobile_orders", "mobile_sims", "mobile_customers",
        "digicloud_phone_numbers", "digicloud_reseller_device_models",
        "digicloud_managed_user_domains", "digicloud_domains",
        "digicloud_organization_settings", "portability_snapshots",
        "port_timeline_events", "port_draft_revisions",
        "port_submission_attempts", "port_drafts", "trusted_devices",
        "notification_events", "audit_logs", "organization_modules",
        "role_permissions", "user_roles", "mobile_sync_states",
        "mobile_plans", "users", "roles", "permissions", "organizations",
    ]
    for table in tables:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
