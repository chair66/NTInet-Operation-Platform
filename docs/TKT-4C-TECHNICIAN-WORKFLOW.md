# NOP v1.18.0 — TKT-4C Technician Workflow

## My Work

`Support > My Work` is the mobile-first field view for technicians. Field Technician accounts see only jobs where they are the primary technician or additional crew. Work is grouped into Active Now, Today's Schedule, and Upcoming & Unscheduled.

Each work card provides the appointment, service address, priority, current status, directions, customer calling, internal instructions, and access to the full work order.

## Guided workflow

- Scheduled or Dispatched → Start Travel or Arrived
- En Route → Arrived
- On Site → Start Work
- In Progress → Pause, Needs Follow-Up, or Complete
- Paused → Resume Work or Needs Follow-Up
- Follow-Up Required → Resume Work

Pause and follow-up require a technician note. Completion requires a completion summary. Invalid workflow jumps are rejected by the server even if a request is submitted outside the interface.

## Records and security

Every technician update records job activity and an audit event. Travel, arrival, start, and completion timestamps are retained. Completion and follow-up updates also add an internal note to a linked support ticket.

The existing `jobs.technician` permission authorizes the workflow. The existing job scope restricts non-dispatch technicians to their assignments. Administrative status overrides remain available only to users with `jobs.manage`.

No database migration is required. Alembic remains at `20260806_11 (head)`.
