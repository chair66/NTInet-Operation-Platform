# NOP v1.13.1 — TKT-3B.1 Bandwidth Messaging Production Integration

## What this release adds

NOP now accepts Bandwidth inbound-message callbacks and outbound delivery receipts. Callback events are idempotent, so Bandwidth retries do not duplicate messages. Customer and ticket SMS records progress through sending, sent, delivered, or failed states. Inbound replies are attached to the latest matching conversation, and STOP/START keywords update the contact's SMS consent.

## Install

```powershell
cd C:\Users\chair\Documents\ntinet-operations-platform
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected migration: `20260806_08 (head)`.

## Create the webhook secret

Generate a long random value in PowerShell:

```powershell
-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 48 | ForEach-Object {[char]$_})
```

Add the result to `.env`:

```dotenv
BANDWIDTH_MESSAGING_WEBHOOK_SECRET=your-random-value
```

Restart NOP after changing `.env`.

## Bandwidth callback URLs

NOP must be available through a public HTTPS hostname. Replace `support.ntinet.com` and `YOUR_SECRET` below with the deployed hostname and the secret from `.env`.

Inbound callback URL:

```text
https://support.ntinet.com/api/webhooks/bandwidth/messaging/inbound/YOUR_SECRET
```

Outbound callback URL:

```text
https://support.ntinet.com/api/webhooks/bandwidth/messaging/outbound/YOUR_SECRET
```

Configure both URLs on the Bandwidth Messaging Application associated with the SMS profile's application ID. The endpoints return HTTP 204 after committing the callback. An invalid secret returns 404.

For temporary Windows testing, an HTTPS tunnel such as ngrok can expose local port 8000. A stable HTTPS hostname on the Ubuntu deployment is recommended for production.

## Acceptance test

1. Send an SMS from a customer page.
2. Confirm its status changes from Sent to Delivered after the outbound callback.
3. Reply from the customer's handset.
4. Confirm the reply appears as Inbound/Received in Customer Communications.
5. Reply `STOP` and confirm the contact becomes Opted Out.
6. Attempt another SMS and confirm NOP suppresses it unless an authorized override is documented.
7. Reply `START` and confirm consent changes to Consented.

Bandwidth may retry callbacks for up to 24 hours. NOP stores a unique event fingerprint so repeats are safe.
