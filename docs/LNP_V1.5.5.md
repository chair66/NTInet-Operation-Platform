# LNP v1.5.5 — System Diagnostics

- Adds Administration → System Diagnostics.
- Tests database, Bandwidth API connectivity, and SMTP connection/authentication.
- Adds a safe Send Test Email action that does not create or submit a port order.
- Displays non-sensitive SMTP configuration only.
- Reuses the production notification delivery path to make the test meaningful.
- Renames the prior diagnostics navigation item to API Log.
- No database migration or new tables.
