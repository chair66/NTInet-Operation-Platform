# NOP v1.14.0 — TKT-3C Unified Communications Inbox

## Included

- Shared email and SMS conversation inbox
- Expandable chronological threads instead of one long message table
- Customer, contact, channel, status, assignment, unread, and ticket context
- Search and filters for unread, open, waiting, closed, SMS, email, mine, and unassigned
- Direct conversation replies using the assigned communication profile
- SMS consent enforcement and authorized override documentation
- Mark read, assign, close/reopen, link ticket, and create-ticket actions
- Expandable conversation cards on customer profiles
- Existing-message backfill into threads
- Provider-neutral email threading fields for inbound mailbox synchronization

## Install

```powershell
cd C:\Users\chair\Documents\ntinet-operations-platform
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected migration:

```text
20260806_09 (head)
```

Restart NOP and open **Communications Inbox** in the navigation.

## Threading behavior

SMS messages group by customer and contact. Email messages group by customer, contact, and normalized subject, so `Service Update`, `Re: Service Update`, and `Fwd: Service Update` share a thread. Ticket-linked replies remain attached to their conversation and ticket.

Existing communication records remain the source messages. The migration creates conversation summaries and links each existing record to its conversation.

## Inbound email connector

This release includes the inbox, email conversation grouping, and storage for `Message-ID`, `In-Reply-To`, and `References`. Outbound email is immediately shown in the inbox. Actual inbound email retrieval requires the next connector step after choosing the mailbox provider:

- Microsoft 365: Microsoft Graph
- Google Workspace/Gmail: Gmail API
- Other hosted mailboxes: IMAP

Inbound SMS continues through the Bandwidth callbacks added in TKT-3B.1.
