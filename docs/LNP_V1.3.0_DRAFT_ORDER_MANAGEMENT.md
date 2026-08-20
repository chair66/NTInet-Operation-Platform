# LNP v1.3.0 – Draft Order Management

## Included
- Persistent organization-scoped port drafts with NTInet reference numbers.
- Save Draft from the customer-information and review screens.
- Draft work queue and draft detail pages.
- Resume and edit saved drafts.
- Automatic draft creation before review and before live submission.
- Automatic failed-submission preservation.
- Submission-attempt history containing request, response, status, error code, and error message.
- Successful submissions link the local draft to the Bandwidth order ID.
- E.164 normalization for porting TNs, BTN, and replacement BTN before API submission.

## Database
New tables are created at startup through SQLAlchemy metadata:
- `port_drafts`
- `port_submission_attempts`

For production PostgreSQL, create an Alembic migration before deployment.
