# NTInet Operations Platform LNP v1.5.0
## Intelligent Draft Management & Port Order Timeline

### Included
- OnePort portability refresh whenever an existing draft is opened for correction.
- Mandatory OnePort verification immediately before submission.
- Submission is paused when portability changes or cannot be verified.
- Change detection for earliest FOC, losing carrier, port type, number type, and rate center.
- Persistent portability snapshots containing the raw response and normalized summary.
- Draft revision history on every save.
- Port order timeline events for creation, verification, changes, failures, and submission.
- Draft health indicators: Current, Portability Changed, and Requires Attention.
- Existing drafts are upgraded naturally: opening Correct and Submit refreshes and stores current OnePort data.

### Database
Three additive tables are created automatically by SQLAlchemy:
- `port_draft_revisions`
- `port_timeline_events`
- `portability_snapshots`

No existing draft or submission-attempt data is removed.
