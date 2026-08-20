# PLAT-004A — Organization Core & Service Layer

## Purpose

PLAT-004A establishes organizations as the central administrative record for the NTInet Operations Platform. The supported organization types are intentionally limited to `staff` and `reseller`.

## Included

- `OrganizationService` for organization lifecycle and validation
- Search, filters, sorting, and pagination
- Organization detail page
- Active, suspended, disabled, and deleted states
- Soft delete and restore
- Organization statistics and simple health assessment
- Duplicate-name prevention and unique slug generation
- Structured audit events and notification-outbox events
- Staff-only server-side authorization

## Database changes

The `organizations` table gains:

- `display_name`
- `status`
- `notes`
- `deleted_at`
- `deleted_by_user_id`

SQLite development databases are upgraded automatically by `init_database()`. Production databases should use an equivalent Alembic migration.

## Lifecycle behavior

- **Active:** organization and normal module access are enabled.
- **Suspended:** organization is inactive until re-enabled.
- **Disabled:** organization is inactive until re-enabled.
- **Deleted:** soft-deleted; historical records remain available.
- Restored organizations return as **Disabled** so staff can review them before activation.
- Deleting an organization disables its users but does not delete them.
- The current staff organization cannot be deleted by its own administrator.

## Health assessment

Health is calculated at request time:

- **Critical:** deleted, disabled, suspended, or otherwise inactive.
- **Warning:** no active users, no enabled modules, or a reseller has no Bandwidth sites assigned.
- **Healthy:** no current checks report a problem.

Provider connectivity tests are not part of PLAT-004A.

## Validation

```powershell
python -m compileall .\app
python -c "from app.services import OrganizationService; from app.routers.identity import router; print('PLAT-004A imports OK')"
```

## Rollback

Restore the backed-up versions of:

- `app/database/models.py`
- `app/database/core.py`
- `app/services/__init__.py`
- `app/routers/identity.py`
- `app/templates/admin/organizations.html`

Remove:

- `app/services/organization_service.py`
- `app/templates/admin/organization_detail.html`

The added SQLite columns may remain without affecting the prior application version.
