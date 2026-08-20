# TKT-4F — Estimate Options, Templates, Documents, and Email Delivery

## Delivered

- Estimates support any number of freely named, independently totaled options.
- Each option has its own line items, customer notes, cost, gross profit, and margin.
- Labor quantities use 0.5-hour increments; non-labor quantities remain whole numbers.
- Print and PDF actions can include one or several selected options while keeping every option total separate.
- The email composer supports multiple customer contacts, selected estimate options, an editable subject and message, and saved templates.
- Proposal PDFs and estimate documents can be attached to outbound email.
- Shared Document Storage provides reusable files that can be attached to estimates.
- Estimate delivery history records each recipient, selected options, included documents, status, and communication record.
- Estimate-to-job conversion copies a single selected option so alternatives are never combined accidentally.

SMS proposal delivery is intentionally excluded from this release.

## Email template tokens

- `{{contact_first_name}}`
- `{{contact_name}}`
- `{{customer_name}}`
- `{{estimate_number}}`
- `{{estimate_title}}`
- `{{option_names}}`
- `{{sender_name}}`

## Deployment

From the activated virtual environment:

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

The expected migration is `20260807_16 (head)`. Restart NOP after the migration completes.

Uploaded files are stored beneath the configured `DOCUMENT_STORAGE_DIR`, which defaults to `var/document_storage`. Preserve and back up this directory alongside PostgreSQL.

## Acceptance checks

1. Create an estimate and add Monthly Recurring and Non-Recurring options.
2. Add different catalog items to each option and confirm the totals remain independent.
3. Add customer-facing notes to each option and general notes to the estimate.
4. Upload a document in Document Storage and attach it to the estimate.
5. Open Email Proposal, select multiple contacts and options, edit the subject/body, attach the PDF and document, and send.
6. Confirm each recipient receives a PDF containing only the selected options and that Delivery History records the result.
