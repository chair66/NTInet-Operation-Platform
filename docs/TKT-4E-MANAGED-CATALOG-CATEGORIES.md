# TKT-4E Hotfix — Managed Catalog Categories

Version 1.20.1 replaces free-text catalog categories with organization-scoped managed category records.

## Included

- Dedicated **Catalog Categories** page available to catalog managers.
- Add, rename, activate, and deactivate categories.
- Catalog-item entry uses a required category dropdown; arbitrary values can no longer be entered.
- Category names are unique without regard to letter case at the service layer.
- Renaming a category updates the displayed category on all linked catalog items.
- Inactive categories remain attached to existing items but cannot be assigned to new items.
- Migration preserves existing category names, merges case-only variations, and assigns blank legacy values to **Uncategorized**.

## Upgrade

Run `python -m alembic upgrade head`. The expected revision is `20260807_14 (head)`.
