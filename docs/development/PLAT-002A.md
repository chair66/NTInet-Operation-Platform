# PLAT-002A — Centralized Security Dependencies

## Status

Ready for implementation.

## Priority

P0 — Security critical.

## Objective

Create the centralized authentication and authorization dependency framework used by protected FastAPI routes.

PLAT-002A does not remove the current path-based authorization middleware. Existing routes will be migrated after organization scoping is implemented.

## Required authorization order

1. Authentication
2. Active user
3. Active organization
4. Organization type, when applicable
5. Module access
6. Permission
7. Resource organization scope
8. Business logic

Resource organization scope is scheduled for PLAT-002B.

## Included components

- `SecurityContext`
- Authentication dependencies
- Active-user validation
- Active-organization validation
- Staff-only and reseller-only dependencies
- Module authorization dependency
- Permission authorization dependencies
- Organization-type validation

## Superuser rules

A superuser may bypass module assignment and permission checks. A superuser may not bypass authentication, active-user status, active-organization status, or staff/reseller organization classification.

## Validation

```powershell
python -m compileall .\app
python -c "from app.security import SecurityContext, require_staff, require_reseller, require_module, require_permission; print('PLAT-002A imports OK')"
python -c "from app.database.models import Organization; print(Organization(name='Test', slug='test', organization_type='staff').is_staff)"
python -m uvicorn app.main:app --reload --port 8001
```
