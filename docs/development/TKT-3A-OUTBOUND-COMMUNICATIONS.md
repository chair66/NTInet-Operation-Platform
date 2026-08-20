# TKT-3A Outbound Communications

`ticket_outbound_messages` is the durable delivery ledger. Each email or SMS
has a channel, destination, event type, status, provider, provider message ID,
deduplication key, error, attempt counter, retry time, and lifecycle timestamps.

Messages move through `queued`, `sent`, `delivered`, `failed`, or `suppressed`.
Bandwidth accepts outbound SMS asynchronously, so an HTTP 202 is recorded as
`sent`; TKT-3B webhooks will promote it to `delivered` or `failed`.

Automatic events use deterministic keys. Manual replies use their ticket-entry
ID. A unique database index prevents duplicate delivery if a request repeats.
Failed deliveries receive exponential retry times and are processed on startup
or through the authorized Retry action.

Technician assignment changes generate direct staff email records. On startup,
open assigned tickets past their SLA target generate one deduplicated SLA alert
per SLA target timestamp.

Test mode records simulated provider IDs without invoking SMTP or Bandwidth.
