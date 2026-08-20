# NOP v1.17.0 — TKT-4B Calendar and Dispatch Board

## Daily dispatch board

The staff-only Dispatch Board displays one horizontal schedule lane per NTInet technician plus an Unassigned lane. The daily timeline runs from 7:00 AM through 8:00 PM with quarter-hour grid lines.

- Drag an unscheduled job from the queue onto a technician lane.
- Drag an existing scheduled job to a new time or technician.
- Drop times are rounded to the nearest 15 minutes.
- Job duration controls the visual width of each appointment.
- Cards are color-coded by priority and link directly to the full work order.
- Every move updates the job schedule, primary technician, status, audit log, and job activity history.

## Conflict protection

NOP checks the primary technician and crew assignments for overlapping active work. A conflict displays the existing job numbers and requires explicit confirmation before the dispatcher can schedule over them.

## Board navigation

- Previous, Today, and Next controls
- Day and Week views
- Technician filtering
- Weekly technician-by-day overview
- Unscheduled queue remains visible alongside either view

## Security

The Field Service module remains restricted to NTInet staff organizations. The Dispatch Board requires `jobs.dispatch`; restricted Field Technician accounts cannot view or change the schedules of other technicians.

## Database

TKT-4B uses the TKT-4A job, assignment, and activity schema. No additional migration is required. Alembic remains at `20260806_11 (head)`.
