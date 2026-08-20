# LNP v1.5.4 - Order Workflow Improvements

- Submitted orders no longer appear in the active Drafts list.
- Newly submitted local orders are merged into Orders and Recent Port Requests while provider list synchronization catches up.
- Dashboard cards now show Open Orders, Draft Orders, FOC Orders, and Exceptions.
- Dashboard cards link directly to their filtered operational queues.
- Port Orders now supports All, Open, Drafts, FOC, Exceptions, and Completed navigation.
- Exception/order detail pages include Correct and Resubmit.
- Drafts can be permanently deleted with confirmation.
- Submission confirmation email support added using SMTP environment settings.

## SMTP settings

`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_SSL`, and `PORT_NOTIFICATION_EMAIL`.
