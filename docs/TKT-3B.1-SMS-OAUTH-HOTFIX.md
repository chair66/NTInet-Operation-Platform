# NOP v1.12.1 — SMS OAuth Hotfix

This hotfix changes ticket and customer SMS delivery to the OAuth client-credentials flow already used by NOP's Bandwidth porting integration.

## Install on Windows

From PowerShell in the NOP project directory:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

The current migration should report `20260806_07 (head)`. Restart NOP after the migration.

## NTInet SMS profile

Edit the SMS communication profile and confirm:

- Authentication: `NOP system OAuth credentials (.env)`
- Messaging API base: `https://messaging.bandwidth.com/api/v2`
- Bandwidth account ID: the Messaging account/user ID
- Messaging application ID: the application attached to the sending number
- Originating phone number: the Bandwidth number in E.164 or ten-digit US format

Existing staff-owned profiles default to system OAuth after migration. The system option reads the existing `BANDWIDTH_CLIENT_ID`, `BANDWIDTH_CLIENT_SECRET`, and `BANDWIDTH_TOKEN_URL` settings, so the secret does not need to be entered again.

Use **Test** on the profile. It obtains and validates an OAuth token but does not send an SMS. Then send one live test from a customer page. The token and message calls appear under **Administration → API Log**, with tokens and message text redacted.

Inbound and delivery-status callback endpoints are not part of this hotfix; they remain the next communications task.
