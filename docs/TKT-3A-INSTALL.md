# TKT-3A Outbound Communications installation

Install over NOP v1.9.0 and run `python -m alembic upgrade head`. Expected
revision: `20260806_04 (head)`.

TKT-3A defaults to safe simulation mode. No external message is sent until
test mode is disabled and the corresponding live channel is enabled.

```env
TICKET_COMMUNICATION_TEST_MODE=true
TICKET_EMAIL_ENABLED=false
TICKET_SMS_ENABLED=false
TICKET_AUTO_NEW_CONFIRMATION=true
TICKET_AUTO_STATUS_NOTIFICATIONS=true
TICKET_PUBLIC_BASE_URL=http://127.0.0.1:8000
```

Existing SMTP settings are reused. Bandwidth SMS requires:

```env
BANDWIDTH_MESSAGING_API_BASE=https://messaging.bandwidth.com/api/v2
BANDWIDTH_MESSAGING_USERNAME=
BANDWIDTH_MESSAGING_PASSWORD=
BANDWIDTH_MESSAGING_APPLICATION_ID=
BANDWIDTH_MESSAGING_FROM_NUMBER=
```

Test the complete ticket workflow first. The Communications page must show the
providers as ready. For production, set the public base URL to the externally
reachable NOP URL, then deliberately set test mode false and enable each
verified channel.

SMS requires the selected contact to have a valid US mobile number and
`consented` SMS status. Only users with `tickets.communication_override` can
override that rule for an individual message.
