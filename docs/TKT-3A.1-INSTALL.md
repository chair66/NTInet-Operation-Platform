# TKT-3A.1 Multi-Organization Communication Profiles

Install over NOP v1.10.0, activate the virtual environment, and apply the
database migration:

```powershell
cd C:\Users\chair\Documents\ntinet-operations-platform
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected revision: `20260806_05 (head)`.

Keep these safety settings while profiles are being configured and tested:

```env
TICKET_COMMUNICATION_TEST_MODE=true
TICKET_EMAIL_ENABLED=false
TICKET_SMS_ENABLED=false
```

Restart NOP, then open **Administration → Communication Profiles**. Create an
email or SMS profile for each organization/module identity. Credentials are
encrypted with `APP_SECRET_KEY`; back up that value and do not change it after
saving credentials.

Profile routing order is:

1. Profile explicitly selected on the ticket.
2. Owning organization's Support Tickets default.
3. Owning organization's organization-wide default.
4. Shared NTInet Support Tickets default.
5. Shared NTInet organization-wide default.

Reseller administrators can manage only their own organization's profiles.
Profiles owned by NTInet are available to other organizations only when
**Allow other organizations to use this profile** is enabled. Secrets are
never shown again after saving.

Use the profile **Test** action and complete ticket tests in safe mode first.
When ready for live delivery, deliberately set `TICKET_COMMUNICATION_TEST_MODE`
to `false` and enable only the verified channel. SMS consent and destination
validation from TKT-3A remain enforced.
