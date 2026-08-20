# NOP v1.15.0 — TKT-3C.1 GreenGeeks Inbound Email

## What this release does

- Polls each enabled GreenGeeks mailbox through IMAP in read-only mode using `BODY.PEEK[]`.
- Groups replies with their existing email conversation using standard `Message-ID`, `In-Reply-To`, and `References` headers.
- Falls back to a unique customer-contact email match when the reply headers are unavailable.
- Adds a customer-reply entry to the linked ticket timeline.
- Creates an unread in-app notification for the assigned staff or reseller user and emails that user a reply alert.
- Records every IMAP UID import so polling and retries cannot create duplicate communications.
- Leaves unmatched messages safely recorded for later review instead of assigning them to the wrong customer.

## GreenGeeks setup

Open GreenGeeks cPanel, choose **Email Accounts**, then **Connect Devices** for the support mailbox. Copy the displayed incoming-server hostname. GreenGeeks settings are account-specific, so do not assume a generic hostname.

In NOP, open **Administration → Communication Profiles**, edit the appropriate Email profile, and complete **Inbound email · GreenGeeks IMAP**:

- Enable inbound email synchronization.
- IMAP host: the incoming server shown by GreenGeeks.
- IMAP port: normally `993`.
- Security: `SSL`.
- Username: the complete mailbox email address.
- Password: that mailbox's password.
- Folder: `INBOX`.

Save the profile, run **Test**, then use **Sync Inbox Now**. The background worker checks enabled profiles every 60 seconds by default.

## Environment settings

```env
INBOUND_EMAIL_SYNC_ENABLED=true
INBOUND_EMAIL_SYNC_INTERVAL_SECONDS=60
```

Keep `APP_SECRET_KEY` unchanged after saving credentials because NOP encrypts mailbox passwords with it.

## Upgrade

```powershell
cd C:\Users\chair\Documents\ntinet-operations-platform
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected revision: `20260806_10 (head)`.
