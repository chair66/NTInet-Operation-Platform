# TKT-3B Customer Communications Inbox

Install over NOP v1.11.0 and apply the database migration:

```powershell
cd C:\Users\chair\Documents\ntinet-operations-platform
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected revision: `20260806_06 (head)`.

Restart NOP and open a customer account. The page now provides **Email** and
**SMS** actions, contact-level message buttons, recent communication history,
and a complete history page.

Leave safe test mode enabled during acceptance testing:

```env
TICKET_COMMUNICATION_TEST_MODE=true
TICKET_EMAIL_ENABLED=false
TICKET_SMS_ENABLED=false
```

Test these cases before enabling live delivery:

1. Send email using automatic profile routing.
2. Send SMS to a contact with `consented` SMS status.
3. Confirm unknown or opted-out consent suppresses SMS.
4. Confirm an authorized override requires a written reason.
5. Link a message to an open ticket.
6. Create a new ticket from an unlinked conversation.

The inbox uses the TKT-3A.1 communication profiles and daily limits. Automatic
routing prefers a Customer Management profile, then an organization-wide
default, then a Support Tickets profile. Shared NTInet profiles remain the final
fallback. Every attempt records its sender, destination, status, profile,
provider message ID, consent override, user, and optional ticket.

This release creates the inbound-ready communication record and thread fields.
Provider webhook ingestion for customer replies should be enabled only in a
separate release with provider signature validation and production callback
configuration.
