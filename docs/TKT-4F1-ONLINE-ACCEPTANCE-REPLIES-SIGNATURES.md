# TKT-4F.1 — Online Acceptance, Estimate Replies, and Email Signatures

## Delivered

- Existing estimate option names and customer notes are editable with a single **Save** action.
- Estimate emails include a signed **View & Accept Estimate Online** link.
- The public acceptance page displays only the options included in that recipient's email.
- Customers select the option or options they approve, enter their name and email, acknowledge authorization, and sign on screen.
- A completed acceptance records the selected option IDs, signer, signer email, signature image, date/time, and source IP.
- Accepted estimates move to **Estimate Won** and display the acceptance record in NOP and in generated estimate PDFs.
- Only Estimate Won records can be converted to jobs, and only accepted options are available for conversion.
- Estimate email messages and replies share an estimate-specific customer communication conversation.
- Inbound estimate replies increment the unread communication count and appear in the existing header email/SMS alert.
- Estimate conversations show a link back to their estimate.
- Each user can manage a plain-text email signature and signature photo from **My Account**.
- The user's signature is automatically added to customer communication emails, estimate emails, and ticket emails sent by that user. Automatic ticket emails use the assigned technician's signature when available.

## Production setting

`TICKET_PUBLIC_BASE_URL` must be the externally reachable HTTPS address of NOP, for example:

```text
TICKET_PUBLIC_BASE_URL=https://operations.ntinet.com
```

Do not leave this set to `127.0.0.1` in production or customers will not be able to open their acceptance links.

Signature photos are stored in `USER_SIGNATURE_PHOTO_DIR`, defaulting to `var/user_signature_photos`. Back up this directory along with `DOCUMENT_STORAGE_DIR` and PostgreSQL.

## Deployment

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m alembic current
```

Expected migration:

```text
20260807_17 (head)
```

Restart NOP after migration.

## Acceptance test

1. Open an existing estimate option, change its name, and click **Save**.
2. Email an estimate to a test customer contact.
3. Open the email's acceptance button from a browser that is not signed in to NOP.
4. Select an option, sign, and accept.
5. Confirm the estimate displays **Estimate Won**, signer information, and the accepted option.
6. Convert the accepted option to an existing customer job.
7. Reply to the estimate email and run inbound email sync.
8. Confirm the reply appears in Customer Communications and the header shows an unread email alert.
9. Add a signature and photo under **My Account**, then send a customer or ticket email and verify the signature appears.
