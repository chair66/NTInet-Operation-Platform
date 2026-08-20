# PLAT-003B.2 — User Management UI

## Purpose

PLAT-003B.2 replaces the basic user table with a tenant-aware administration console while retaining the existing FastAPI and Jinja architecture.

## Features

- Server-side search across user name, email, organization, and role
- Filters for account status, MFA status, organization, and role
- Server-side pagination with 10, 25, 50, or 100 rows per page
- Sorting by user, organization, account status, and last login
- Summary cards and responsive status badges
- Consolidated action menu for enable/disable and MFA actions
- Improved empty state and responsive layout
- Updated Add User modal using the existing PLAT-003B.1 service layer

## Security

All user queries continue to pass through `scope_users`. Organization filtering is rejected when the requested organization is outside the administrator's security context. Existing role assignment and tenant-isolation checks remain unchanged.

## Database changes

None.

## Deferred to PLAT-003B.3

- Dedicated user detail/editor screen
- Invitation emails
- Administrative password reset workflow
- Force-password-change flag
- Account unlock controls
