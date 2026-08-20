from collections.abc import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _sqlite_milestone_45_upgrade() -> None:
    """Small compatibility upgrade for development databases created by Milestone 4.

    Production PostgreSQL deployments should use Alembic before rollout.
    """
    if not settings.database_url.startswith("sqlite"):
        return
    schema = inspect(engine)
    with engine.begin() as conn:
        if "organizations" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("organizations")}
            if "mfa_policy" not in columns:
                conn.execute(text("ALTER TABLE organizations ADD COLUMN mfa_policy VARCHAR(20) NOT NULL DEFAULT 'optional'"))
            if "bandwidth_site_ids" not in columns:
                conn.execute(text("ALTER TABLE organizations ADD COLUMN bandwidth_site_ids TEXT NOT NULL DEFAULT '[]'"))
            additions = {
                "display_name": "VARCHAR(120)",
                "is_protected": "BOOLEAN NOT NULL DEFAULT 0",
                "status": "VARCHAR(20) NOT NULL DEFAULT 'active'",
                "notes": "TEXT NOT NULL DEFAULT ''",
                "deleted_at": "DATETIME",
                "deleted_by_user_id": "INTEGER",
                "password_expiration_days": "INTEGER NOT NULL DEFAULT 0",
                "session_timeout_minutes": "INTEGER NOT NULL DEFAULT 480",
                "allow_api_access": "BOOLEAN NOT NULL DEFAULT 0",
                "timezone": "VARCHAR(64) NOT NULL DEFAULT 'America/New_York'",
                "date_format": "VARCHAR(20) NOT NULL DEFAULT 'MM/DD/YYYY'",
                "default_role_id": "INTEGER",
            }
            for name, ddl in additions.items():
                if name not in columns:
                    conn.execute(text(f"ALTER TABLE organizations ADD COLUMN {name} {ddl}"))
            conn.execute(text("UPDATE organizations SET status = CASE WHEN active = 1 THEN 'active' ELSE 'disabled' END WHERE status IS NULL OR status = ''"))
        if "users" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("users")}
            additions = {
                "mfa_enabled": "BOOLEAN NOT NULL DEFAULT 0",
                "mfa_required": "BOOLEAN NOT NULL DEFAULT 0",
                "mfa_secret_encrypted": "TEXT",
                "mfa_recovery_hashes": "TEXT NOT NULL DEFAULT '[]'",
                "mfa_enrolled_at": "DATETIME",
                "force_password_change": "BOOLEAN NOT NULL DEFAULT 0",
                "password_changed_at": "DATETIME",
                "locked_at": "DATETIME",
                "deleted_at": "DATETIME",
                "deleted_by_user_id": "INTEGER",
                "invitation_token_hash": "VARCHAR(64)",
                "invitation_expires_at": "DATETIME",
            }
            for name, ddl in additions.items():
                if name not in columns:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
        if "digicloud_organization_settings" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("digicloud_organization_settings")}
            if "provisioning_server" not in columns:
                conn.execute(text("ALTER TABLE digicloud_organization_settings ADD COLUMN provisioning_server VARCHAR(255) NOT NULL DEFAULT ''"))
            additions = {
                "billing_model": "VARCHAR(20) NOT NULL DEFAULT 'direct'",
                "platypus_parent_customer_id": "VARCHAR(40) NOT NULL DEFAULT ''",
                "wholesale_rate_group_ids": "TEXT NOT NULL DEFAULT '[]'",
                "default_wholesale_rate_group_id": "VARCHAR(20) NOT NULL DEFAULT ''",
            }
            for name, ddl in additions.items():
                if name not in columns:
                    conn.execute(text(f"ALTER TABLE digicloud_organization_settings ADD COLUMN {name} {ddl}"))
        if "digicloud_reseller_device_models" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("digicloud_reseller_device_models")}
            if "api_model_value" not in columns:
                conn.execute(text("ALTER TABLE digicloud_reseller_device_models ADD COLUMN api_model_value VARCHAR(120) NOT NULL DEFAULT ''"))
        if "port_drafts" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("port_drafts")}
            additions = {
                "submitted_by_user_id": "INTEGER",
                "notification_email": "VARCHAR(255) NOT NULL DEFAULT ''",
                "notifications_enabled": "BOOLEAN NOT NULL DEFAULT 1",
                "notification_state_json": "TEXT NOT NULL DEFAULT '{}'",
            }
            for name, ddl in additions.items():
                if name not in columns:
                    conn.execute(text(f"ALTER TABLE port_drafts ADD COLUMN {name} {ddl}"))
        if "audit_logs" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("audit_logs")}
            if "module" not in columns:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN module VARCHAR(80) NOT NULL DEFAULT ''"))
            if "event_data" not in columns:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN event_data TEXT NOT NULL DEFAULT '{}'"))



def _port_notification_schema_upgrade() -> None:
    """Ensure Sprint 4.3.2h port-notification columns exist on all supported DBs.

    This is intentionally idempotent so development PostgreSQL installs that
    replace the app folder without running a separate migration do not break
    the porting UI at startup. Production can still apply the bundled SQL
    migration normally.
    """
    schema = inspect(engine)
    if "port_drafts" not in schema.get_table_names():
        return
    columns = {c["name"] for c in schema.get_columns("port_drafts")}
    is_sqlite = settings.database_url.startswith("sqlite")
    additions = {
        "submitted_by_user_id": "INTEGER",
        "notification_email": "VARCHAR(255) NOT NULL DEFAULT ''",
        "notifications_enabled": ("BOOLEAN NOT NULL DEFAULT 1" if is_sqlite else "BOOLEAN NOT NULL DEFAULT TRUE"),
        "notification_state_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    with engine.begin() as conn:
        for name, ddl in additions.items():
            if name not in columns:
                conn.execute(text(f"ALTER TABLE port_drafts ADD COLUMN {name} {ddl}"))

def init_database() -> None:
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _sqlite_milestone_45_upgrade()
    _port_notification_schema_upgrade()
