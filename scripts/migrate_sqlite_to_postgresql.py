"""One-time, non-destructive NOP SQLite to PostgreSQL data migration.

The PostgreSQL schema must already exist via ``alembic upgrade head``. The
source SQLite database is opened read-only and is never modified.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sqlite3
import sys

from sqlalchemy import Boolean, DateTime, MetaData, Numeric, create_engine, func, select
from sqlalchemy.engine import Connection

# Support direct execution from the project root on Windows.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings


TABLE_ORDER = [
    "organizations",
    "permissions",
    "roles",
    "users",
    "user_roles",
    "role_permissions",
    "organization_modules",
    "audit_logs",
    "notification_events",
    "trusted_devices",
    "port_drafts",
    "port_submission_attempts",
    "port_draft_revisions",
    "port_timeline_events",
    "portability_snapshots",
    "digicloud_organization_settings",
    "digicloud_domains",
    "digicloud_managed_user_domains",
    "digicloud_phone_numbers",
    "digicloud_reseller_device_models",
    "mobile_plans",
    "mobile_sync_states",
    "mobile_customers",
    "mobile_sims",
    "mobile_orders",
    "mobile_exceptions",
    "mobile_lines",
    "mobile_port_requests",
]

DEFERRED_COLUMNS = {
    "organizations": {"deleted_by_user_id", "default_role_id"},
    "users": {"deleted_by_user_id"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite",
        type=Path,
        default=Path("ntiops.db"),
        help="Path to the source SQLite database (default: ntiops.db)",
    )
    parser.add_argument(
        "--allow-other-database",
        action="store_true",
        help="Allow a destination other than nop_test or nop_development",
    )
    return parser.parse_args()


def sqlite_connection(path: Path) -> sqlite3.Connection:
    resolved = path.resolve()
    if not resolved.is_file():
        raise SystemExit(f"SQLite source not found: {resolved}")
    connection = sqlite3.connect(
        f"file:{resolved.as_posix()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    return connection


def convert_value(value: object, column) -> object:
    if value is None:
        return None
    if isinstance(column.type, Boolean):
        return bool(value)
    if isinstance(column.type, DateTime):
        if isinstance(value, datetime):
            parsed = value
        else:
            normalized = str(value).strip().replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
        if column.type.timezone and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    if isinstance(column.type, Numeric):
        return Decimal(str(value))
    return value


def ensure_destination_is_safe(connection: Connection, metadata: MetaData) -> None:
    populated = []
    for table_name in TABLE_ORDER:
        table = metadata.tables[table_name]
        count = connection.scalar(select(func.count()).select_from(table))
        if count:
            populated.append(f"{table_name} ({count})")
    if populated:
        raise RuntimeError(
            "Destination must be empty. Populated tables: " + ", ".join(populated)
        )


def source_tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def copy_table(
    source: sqlite3.Connection,
    destination: Connection,
    metadata: MetaData,
    table_name: str,
) -> int:
    table = metadata.tables[table_name]
    source_columns = {
        row[1] for row in source.execute(f'PRAGMA table_info("{table_name}")')
    }
    destination_columns = {column.name for column in table.columns}
    missing = destination_columns - source_columns
    if missing:
        raise RuntimeError(
            f"{table_name}: SQLite source is missing destination columns: "
            + ", ".join(sorted(missing))
        )

    deferred = DEFERRED_COLUMNS.get(table_name, set())
    records = []
    for source_row in source.execute(f'SELECT * FROM "{table_name}"'):
        record = {}
        for column in table.columns:
            value = None if column.name in deferred else source_row[column.name]
            record[column.name] = convert_value(value, column)
        records.append(record)

    if records:
        destination.execute(table.insert(), records)
    return len(records)


def apply_deferred_links(
    source: sqlite3.Connection,
    destination: Connection,
    metadata: MetaData,
) -> None:
    for table_name, column_names in DEFERRED_COLUMNS.items():
        table = metadata.tables[table_name]
        primary_key = list(table.primary_key.columns)
        if len(primary_key) != 1:
            raise RuntimeError(f"Deferred update requires one primary key: {table_name}")
        key = primary_key[0]
        selected = ", ".join([f'"{key.name}"', *[f'"{c}"' for c in column_names]])
        for row in source.execute(f'SELECT {selected} FROM "{table_name}"'):
            values = {
                column_name: row[column_name]
                for column_name in column_names
                if row[column_name] is not None
            }
            if values:
                destination.execute(
                    table.update().where(key == row[key.name]).values(**values)
                )


def reset_sequences(destination: Connection, metadata: MetaData) -> None:
    preparer = destination.dialect.identifier_preparer
    for table_name in TABLE_ORDER:
        table = metadata.tables[table_name]
        if "id" not in table.c or not table.c.id.primary_key:
            continue
        if table.c.id.type.python_type is not int:
            continue
        quoted = preparer.quote(table_name)
        destination.exec_driver_sql(
            "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {quoted}), 1), "
            f"EXISTS(SELECT 1 FROM {quoted}))",
            (table_name,),
        )


def main() -> None:
    args = parse_args()
    settings = get_settings()
    destination_engine = create_engine(settings.database_url, pool_pre_ping=True)
    database_name = destination_engine.url.database or ""
    if (
        database_name not in {"nop_test", "nop_development"}
        and not args.allow_other_database
    ):
        raise SystemExit(
            f"Refusing destination database '{database_name}'. Use nop_test or "
            "nop_development, or explicitly pass --allow-other-database."
        )

    source = sqlite_connection(args.sqlite)
    metadata = MetaData()
    metadata.reflect(bind=destination_engine)
    missing_destination = set(TABLE_ORDER) - set(metadata.tables)
    missing_source = set(TABLE_ORDER) - source_tables(source)
    if missing_destination:
        raise SystemExit(
            "PostgreSQL schema is incomplete; run 'alembic upgrade head'. Missing: "
            + ", ".join(sorted(missing_destination))
        )
    if missing_source:
        raise SystemExit(
            "SQLite source is missing expected tables: "
            + ", ".join(sorted(missing_source))
        )

    copied: dict[str, int] = {}
    try:
        with destination_engine.begin() as destination:
            ensure_destination_is_safe(destination, metadata)
            for table_name in TABLE_ORDER:
                copied[table_name] = copy_table(
                    source, destination, metadata, table_name
                )
                print(f"Copied {table_name}: {copied[table_name]}")
            apply_deferred_links(source, destination, metadata)
            reset_sequences(destination, metadata)
    finally:
        source.close()

    print(f"Migration completed: {sum(copied.values())} total rows copied.")
    print("Run scripts/validate_postgresql_migration.py before starting NOP.")


if __name__ == "__main__":
    main()
