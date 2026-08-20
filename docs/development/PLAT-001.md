# PLAT-001 — Organization Module Framework

## Objective

Create a single-source-of-truth module framework:

- Module definitions live in `app/modules/registry.py`.
- The database stores only organization-specific enablement.
- Access requires both organization module access and user permission.
- Inactive organizations cannot authenticate.

## Files replaced

- `app/database/models.py`
- `app/database/seed.py`
- `app/modules/registry.py`
- `app/modules/__init__.py`
- `app/main.py`

## Files added

- `app/modules/access.py`
- `docs/development/PLAT-001.md`

## Database change

Creates the `organization_modules` table.

## Scope boundary

Dynamic sidebar rendering is reserved for PLAT-002.
