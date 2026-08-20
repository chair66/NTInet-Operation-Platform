# TKT-2 Core Ticket Management

## Tables

- `tickets`: operational ticket state and customer links
- `ticket_entries`: customer replies, internal notes, status changes, and system events
- `ticket_attachments`: authorized attachment metadata and disk storage references

## Security

Ticket visibility follows the linked customer's owner or servicing organization.
Staff can see all tickets. Nonstaff users see only tickets for customers their
organization owns or services. Direct access to an out-of-scope ticket returns
404 to avoid disclosing its existence.

Permissions are `tickets.read`, `tickets.create`, `tickets.manage`,
`tickets.internal_notes`, and `tickets.attachments`. Module access is controlled
separately through the `support-tickets` organization module assignment.

## Communications boundary

TKT-2 records communications but does not send email or SMS. TKT-3 will deliver
customer-visible entries through configured channels and record delivery state.
