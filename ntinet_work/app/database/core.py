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
        if "audit_logs" in schema.get_table_names():
            columns = {c["name"] for c in schema.get_columns("audit_logs")}
            if "module" not in columns:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN module VARCHAR(80) NOT NULL DEFAULT ''"))
            if "event_data" not in columns:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN event_data TEXT NOT NULL DEFAULT '{}'"))

def init_database() -> None:
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _sqlite_milestone_45_upgrade()
