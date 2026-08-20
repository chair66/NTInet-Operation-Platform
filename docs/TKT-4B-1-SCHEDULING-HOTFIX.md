# NOP v1.17.1 — TKT-4B.1 Scheduling Hotfix

This hotfix corrects appointment persistence and display on work orders and the dispatch board.

## Behavior

- Browser `datetime-local` values are interpreted using the service location time zone.
- PostgreSQL continues to store timezone-aware UTC timestamps.
- Work orders, job lists, and dispatch views convert saved timestamps back to local time.
- Dispatch-board JSON timestamps that already contain an offset remain supported.
- Job-detail edits no longer clear a schedule saved through the appointment card.

No database migration is required. The Alembic revision remains `20260806_11`.
