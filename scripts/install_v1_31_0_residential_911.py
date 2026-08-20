"""Create the v1.31.0 residential-user draft table without touching other schema objects.

Run from the NOP project root with the same virtual environment/.env used by NOP:
    python scripts/install_v1_31_0_residential_911.py
"""
from sqlalchemy import inspect

from app.database.core import engine
from app.database.models import DigiCloudResidentialUserDraft


def main() -> None:
    table = DigiCloudResidentialUserDraft.__table__
    table.create(bind=engine, checkfirst=True)
    names = set(inspect(engine).get_table_names())
    if table.name not in names:
        raise SystemExit(f"Failed to create {table.name}")
    print(f"OK: {table.name} is ready")


if __name__ == "__main__":
    main()
