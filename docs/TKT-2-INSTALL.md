# TKT-2 Core Ticket Management installation

This release requires NOP v1.8.x with PostgreSQL at Alembic revision
`20260806_02`.

## Install

Stop Uvicorn, back up `nop_development` and `.env`, then extract the TKT-2 ZIP
over the project directory. Activate the existing virtual environment and run:

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected revision:

```text
20260806_03 (head)
```

Start NOP:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/tickets`. The staff organization receives the
Support Tickets module automatically. Other organizations must be assigned the
module under Administration > Organizations > Modules.

## Demo data and attachments

Four fictional tickets are created when both settings are true:

```env
SEED_DEMO_CUSTOMERS=true
SEED_DEMO_TICKETS=true
```

Attachments default to `var/ticket_attachments` and are limited to 10 MB:

```env
TICKET_ATTACHMENT_DIR=var/ticket_attachments
TICKET_ATTACHMENT_MAX_BYTES=10485760
```

Back up the attachment directory together with PostgreSQL. Attachment metadata
is stored in PostgreSQL; file bytes are stored on disk.

## Validation

- Create a ticket and verify `TKT-######` numbering.
- Change status, priority, assignment, type, and due date.
- Add a customer-visible reply and a private internal note.
- Upload and download a permitted attachment.
- Open the linked customer and verify its Support Tickets history.
- Verify a nonstaff organization cannot access another organization's ticket.
