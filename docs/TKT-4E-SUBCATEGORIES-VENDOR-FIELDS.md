# TKT-4E Hotfix — Sub-categories and Vendor Details

Version 1.20.2 adds a single managed sub-category level and replaces visible SKU entry with operational purchasing details.

- Categories may be top-level or assigned to one parent category.
- Catalog items select a managed category or sub-category.
- Catalog items include Brand and Model Number.
- Ordering Note stores vendor, account, contact, or special ordering instructions.
- Ordering Link stores an optional validated HTTP/HTTPS product or vendor URL.
- SKU is no longer requested or shown in the main catalog. A hidden internal identifier remains for compatibility with existing estimate and job snapshots.

Run `python -m alembic upgrade head`. Expected revision: `20260807_15 (head)`.
