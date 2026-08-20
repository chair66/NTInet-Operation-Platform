from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.database import SessionLocal, init_database
from app.database.mobile_models import MobilePlan


STARTER_PLANS = (
    {
        "plan_code": "NTIM-TALK",
        "name": "Talk & Text",
        "description": "Unlimited talk and text with no included data.",
        "data_gb": 0,
        "monthly_price": Decimal("0.00"),
        "top_up_price_per_gb": Decimal("7.00"),
    },
    {
        "plan_code": "NTIM-1GB",
        "name": "Connect 1GB",
        "description": "Unlimited talk and text with 1GB of data.",
        "data_gb": 1,
        "monthly_price": Decimal("0.00"),
        "top_up_price_per_gb": Decimal("7.00"),
    },
    {
        "plan_code": "NTIM-5GB",
        "name": "Select 5GB",
        "description": "Unlimited talk and text with 5GB of data.",
        "data_gb": 5,
        "monthly_price": Decimal("0.00"),
        "top_up_price_per_gb": Decimal("7.00"),
    },
    {
        "plan_code": "NTIM-20GB",
        "name": "Premier 20GB",
        "description": "Unlimited talk and text with 20GB of data.",
        "data_gb": 20,
        "monthly_price": Decimal("0.00"),
        "top_up_price_per_gb": Decimal("7.00"),
    },
)


def main() -> None:
    init_database()

    created = 0
    updated = 0

    with SessionLocal() as db:
        for values in STARTER_PLANS:
            plan = db.scalar(
                select(MobilePlan).where(
                    MobilePlan.plan_code == values["plan_code"]
                )
            )

            if plan is None:
                plan = MobilePlan(**values)
                db.add(plan)
                created += 1
            else:
                for field, value in values.items():
                    setattr(plan, field, value)
                plan.active = True
                updated += 1

        db.commit()

    print(
        f"NTI Mobile plan seed complete: {created} created, "
        f"{updated} updated."
    )
    print(
        "Starter monthly prices are intentionally $0.00 until final "
        "retail pricing is approved."
    )


if __name__ == "__main__":
    main()
