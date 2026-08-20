# TKT-4E — Estimate and Job Documents

Version 1.21.0 adds type-aware quantities and customer document delivery.

## Quantity rules

- Labor accepts one decimal place in 0.5-hour (30-minute) increments.
- Products and all other catalog types use whole-number quantities.
- Rules are enforced in the browser and by the service layer.

## Financial display

- Positive or zero gross profit and margin display in green.
- Negative gross profit and margin display in red.

## Estimate documents

- Printable customer estimate with line items, pricing, tax, total, validity, and customer notes.
- Email Estimate action with a list of active customer contacts that have email addresses.
- Branded HTML email template delivered through the existing field-service/default communication profile.

## Job documents

- Printable work order with customer, service location, appointment, work description, items, completion information, and signature areas.
- Email Work Order action with customer contact selection.
- Customer email excludes internal technician instructions and internal financial information.

No database migration is required. Database revision remains `20260807_15`.
