# PLAT-004B — Organization Settings and Module Assignment

## Summary

PLAT-004B extends Organization Management with staff-controlled module assignments, organization security policies, and defaults for newly created users.

## Features

### Module assignment

NTInet staff can enable or disable registered modules for each organization. The module registry remains the source of truth. Staff-only modules cannot be assigned to reseller organizations.

New organizations receive Dashboard by default. Staff organizations also receive Administration. An active organization must retain at least one enabled module.

### Security policy

Each organization now stores:

- MFA policy: optional or required
- Password expiration period
- Session timeout in minutes
- Organization API-access flag

Changing MFA to required marks all current, non-deleted users in the organization as MFA required.

### Organization defaults

Each organization now stores:

- IANA time zone
- Date format
- Default role for new users

The default-role field is restricted to system roles or roles owned by the selected organization.

## Database changes

New columns on `organizations`:

- `password_expiration_days`
- `session_timeout_minutes`
- `allow_api_access`
- `timezone`
- `date_format`
- `default_role_id`

SQLite development databases are upgraded during startup. Production PostgreSQL deployments should apply an equivalent Alembic migration before rollout.

## Security rules

- Only NTInet staff superusers can change organization settings or module assignments.
- `administration` is staff-only and cannot be assigned to reseller organizations.
- Deleted organizations cannot be changed.
- Active organizations must have at least one enabled module.
- User permissions continue to apply inside enabled modules.

## Validation

```powershell
python -m compileall .\app
python -c "from app.services.organization_service import OrganizationService; from app.routers.identity import router; print('PLAT-004B imports OK')"
```

Open an organization at `/admin/organizations/{id}` and test the Modules and Security & Defaults tabs.

## Rollback

Restore the pre-PLAT-004B versions of:

- `app/database/models.py`
- `app/database/core.py`
- `app/modules/registry.py`
- `app/services/organization_service.py`
- `app/routers/identity.py`
- `app/templates/admin/organization_detail.html`

The additional database columns may remain unused during a code rollback.
