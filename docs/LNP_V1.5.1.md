# NTInet Operations Platform LNP v1.5.1

## Lean Draft Verification

- Uses one verification state: ready, changed, or failed.
- Removes contradictory success and failure banners.
- Treats missing OnePort metadata in older drafts as hydration, not a change.
- Shows only meaningful field changes.
- Clears stale attention states after a successful unchanged refresh.
- Keeps the existing v1.5.0 tables and timeline; no new database migration is required.
- Fixes the stray `ms` diagnostic label when latency is absent.
