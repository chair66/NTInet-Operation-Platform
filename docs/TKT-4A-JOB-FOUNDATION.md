# NOP v1.16.0 — TKT-4A Job Foundation

## Scope

TKT-4A introduces the persistent job/work-order layer that the visual dispatch board will use in TKT-4B.

- Every job is owned by the protected NTInet staff organization.
- Scheduling and dispatch routes are restricted to staff organizations.
- A customer and active service location are required.
- A job may be created directly or linked to a support ticket.
- One ticket may have multiple jobs.
- Jobs support a primary technician and additional crew members.
- Contract technicians use the restricted Field Technician role and see only assigned jobs.
- Job activity is recorded separately from customer-visible ticket communication.

## Job workflow

Statuses are: Unscheduled, Scheduled, Dispatched, En Route, On Site, In Progress, Paused, Completed, Cancelled, and Follow-Up Required.

Scheduling uses a start, end, and estimated duration. If a start is supplied without an end, NOP calculates the end from the estimated duration.

## Permissions

- `jobs.read`
- `jobs.create`
- `jobs.manage`
- `jobs.dispatch`
- `jobs.technician`

The built-in Operations Admin and Support roles receive dispatch access. The built-in Field Technician role receives assigned-job access only. Reseller roles receive no job permissions, and the Field Service module is staff-only.

## Upgrade

```powershell
cd C:\Users\chair\Documents\ntinet-operations-platform
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected revision: `20260806_11 (head)`.
