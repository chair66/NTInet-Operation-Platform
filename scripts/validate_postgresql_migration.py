"""Validate row counts and primary keys after the NOP PostgreSQL migration."""

from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

from sqlalchemy import MetaData, create_engine, func, select

# Support direct execution from the project root on Windows.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from scripts.migrate_sqlite_to_postgresql import TABLE_ORDER, sqlite_connection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("ntiops.db"))
    return parser.parse_args()


def sqlite_primary_keys(connection: sqlite3.Connection, table_name: str) -> list[str]:
    columns = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return [row[1] for row in sorted(columns, key=lambda row: row[5]) if row[5]]


def normalized_key(row) -> tuple[str, ...]:
    return tuple("" if value is None else str(value) for value in row)


def main() -> None:
    args = parse_args()
    source = sqlite_connection(args.sqlite)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    failures: list[str] = []

    try:
        with engine.connect() as destination:
            for table_name in TABLE_ORDER:
                table = metadata.tables.get(table_name)
                if table is None:
                    failures.append(f"{table_name}: missing from PostgreSQL")
                    continue
                source_count = source.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]
                destination_count = destination.scalar(
                    select(func.count()).select_from(table)
                )
                status = "OK" if source_count == destination_count else "FAILED"
                print(
                    f"{status:6} {table_name}: SQLite={source_count}, "
                    f"PostgreSQL={destination_count}"
                )
                if source_count != destination_count:
                    failures.append(f"{table_name}: row count mismatch")
                    continue

                key_names = sqlite_primary_keys(source, table_name)
                if not key_names:
                    continue
                source_sql = ", ".join(f'"{name}"' for name in key_names)
                source_keys = {
                    normalized_key(row)
                    for row in source.execute(
                        f'SELECT {source_sql} FROM "{table_name}"'
                    )
                }
                destination_keys = {
                    normalized_key(row)
                    for row in destination.execute(
                        select(*(table.c[name] for name in key_names))
                    )
                }
                if source_keys != destination_keys:
                    failures.append(f"{table_name}: primary key mismatch")
    finally:
        source.close()

    if failures:
        print("\nValidation failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("\nValidation passed for every migrated table.")


if __name__ == "__main__":
    main()
