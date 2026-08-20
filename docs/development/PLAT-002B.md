# PLAT-002B — Tenant Isolation

## Security policy

- NTInet staff organizations can access all Bandwidth sub-accounts.
- Reseller organizations can access only explicitly assigned Bandwidth site IDs.
- Reseller database queries are restricted to their organization.
- Cross-organization role assignment is rejected.
- Staff roles cannot be assigned by reseller administrators.
- Platform-wide API diagnostics and organization administration are staff-superuser only.
- CSR and port-out resources remain staff-only because the current Bandwidth responses used by the platform do not expose a reliable reseller site identifier.

## Fail-closed behavior

A reseller with no assigned Bandwidth site IDs sees no Bandwidth sites. Direct URL access to another site returns HTTP 403.

## Database change

Adds `organizations.bandwidth_site_ids` as JSON text. SQLite development databases are upgraded automatically. Production databases require an Alembic migration before deployment.
