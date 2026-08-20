# PLAT-003B.1 — User Services and Backend

## Purpose

PLAT-003B.1 introduces a service layer for user administration. Routers remain responsible for HTTP input/output while services own business rules, tenant enforcement, role validation, MFA administration, and audit creation.

## Added services

- `AuditService`: creates audit records without committing the surrounding transaction and returns tenant-scoped audit history.
- `RoleService`: lists visible roles, validates requested role IDs, assigns roles, and calculates effective permissions.
- `UserService`: lists tenant-scoped users, creates users, changes account status, resets MFA, changes the MFA requirement, and assigns roles.

## Transaction rule

Services do not call `commit()`. The route or job that owns the unit of work commits once after the business operation succeeds. On failure, it rolls back. This ensures that the user change and corresponding audit record are atomic.

## Tenant and privilege rules

- Reseller administrators only see and modify users in their own organization.
- Only a staff superuser can choose another organization during user creation.
- Existing PLAT-002B role-assignment validation remains authoritative.
- Administrators cannot disable their own account.
- Non-superusers cannot change a superuser account.

## Database impact

No schema migration is required.

## Validation

Run:

```powershell
python -m compileall .\app
python -c "from app.services import UserService, RoleService, AuditService; from app.routers.identity import router; print('PLAT-003B.1 imports OK')"
```

## Next milestone

PLAT-003B.2 will build the searchable and paginated user-management interface on this service layer.
