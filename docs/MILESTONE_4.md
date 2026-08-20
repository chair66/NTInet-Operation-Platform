# DigiCloud 2.0 — Milestone 4 Authentication & Multi-Tenant Foundation

## Included

- DigiCloud-branded login and logout
- Argon2 password hashing
- Signed, HTTP-only session cookies
- SQLite development database with PostgreSQL-compatible SQLAlchemy models
- Organizations as the data-scope boundary
- Users with multiple roles
- Roles composed of granular permissions
- Built-in staff and reseller role templates
- Backend permission enforcement for operational routes
- User administration, enable/disable controls
- Organization administration
- Role/permission visibility
- Authentication and administration audit log
- Organization-specific Bandwidth account field

## First launch

Copy `.env.example` to `.env` and set a long random `APP_SECRET_KEY`.
Change `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` before the first launch.
The bootstrap administrator is only created when that email does not already exist.

Install requirements and start:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/login`.

## Role model

Organizations define **which data a user may see**. Roles define **what the user may do**. A user may have multiple roles; effective permissions are combined.

Built-in templates:

- Operations Admin
- Support
- Sales
- Read Only
- Reseller Admin
- Reseller Technician
- Reseller Sales

The bootstrap user is a Super Admin through the `is_superuser` flag.

## Next security work

This milestone establishes the identity and authorization foundation. Before public production deployment, add CSRF tokens to state-changing forms, password reset/change workflows, login throttling, MFA/TOTP, and provider-resource scope assignments for individual Sites and Locations.
