# PLAT-003B.4 — Administration Framework

This release completes the PLAT-003 user-management series and establishes reusable administration components for future organization, inventory, porting, Bandwidth, and NetSapiens modules.

## Included

### Role and permission visibility

- Roles grouped by permission module
- Role-detail view with descriptions and assigned users
- Effective-permission viewer on each user profile
- Tenant-scoped role visibility remains enforced by PLAT-002B

### Bulk user operations

- Enable and disable
- Force password change
- Assign or remove a role
- Soft delete and restore
- User CSV export
- Self-disable and self-delete safeguards
- One structured audit event per bulk operation

### Audit Framework v2

Audit records now support:

- `module`
- JSON `event_data`
- Search by actor, email, action, resource, detail, or IP
- Module, action, organization, and date filters
- CSV export

Existing audit records remain compatible. New columns are added automatically to SQLite development databases.

### Notification outbox foundation

`NotificationService` publishes transactional events to `notification_events` for future delivery through email, Slack, Teams, SMS, GoHighLevel, or in-app notifications. This milestone stores events only; it does not send outbound notifications.

## Database changes

New `audit_logs` columns:

- `module`
- `event_data`

New table:

- `notification_events`

SQLite development databases are upgraded automatically during startup. Production PostgreSQL deployments should receive an equivalent Alembic migration before application deployment.

## Security behavior

- Bulk operations use the existing tenant-scoped `UserService.get_user()` checks.
- Role assignment uses `RoleService.resolve_assignable()` and PLAT-002B role validation.
- Reseller administrators cannot act on users outside their organization.
- Audit searches and exports use organization scoping.
- Role views use scoped role queries.

## Validation

```powershell
python -m compileall .\app
python -c "from app.services import NotificationService, AuditService, RoleService, UserService; from app.routers.identity import router; print('PLAT-003B.4 imports OK')"
```

Test:

- `/admin/users`
- `/admin/users/{id}/edit`
- `/admin/roles`
- `/admin/roles/{id}`
- `/admin/audit`
