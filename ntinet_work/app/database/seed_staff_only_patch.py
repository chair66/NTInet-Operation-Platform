"""
One-time cleanup helper for NTIM-001B.

Run from the project root with:
    python -m app.database.seed_staff_only_patch

This removes any existing NTI Mobile module assignment from reseller
organizations. Normal application startup will continue assigning NTI Mobile
to the protected NTInet staff organization through seed_database().
"""

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.database.models import Organization, OrganizationModule


STAFF_ONLY_MODULES = {"nti-mobile", "administration"}


def main() -> None:
    with SessionLocal() as db:
        reseller_ids = list(
            db.scalars(
                select(Organization.id).where(
                    Organization.organization_type == Organization.RESELLER_TYPE
                )
            )
        )

        if not reseller_ids:
            print("No reseller organizations found. No cleanup required.")
            return

        result = db.execute(
            delete(OrganizationModule).where(
                OrganizationModule.organization_id.in_(reseller_ids),
                OrganizationModule.module_slug.in_(STAFF_ONLY_MODULES),
            )
        )
        db.commit()

        print(
            f"Removed {result.rowcount or 0} staff-only module assignment(s) "
            "from reseller organizations."
        )


if __name__ == "__main__":
    main()
