# Milestone 4.5 — Multi-Factor Authentication

This release adds standards-based TOTP MFA compatible with Microsoft Authenticator, Google Authenticator, Authy, 1Password, Bitwarden, Duo Mobile, and other RFC 6238 applications.

## Included

- QR-code and manual-key enrollment
- MFA challenge after password verification
- Ten single-use recovery codes stored only as Argon2 hashes
- Trusted-browser tokens with a configurable 30-day default lifetime
- Per-organization MFA policy: disabled, optional, or required
- Per-user MFA requirement override
- User self-service security page
- Administrator MFA reset and trusted-device revocation
- Audit events for enrollment, challenges, recovery-code use, trusted devices, policy changes, and resets
- Encryption at rest for TOTP secrets using a key derived from `APP_SECRET_KEY`

## Upgrade notes

1. Back up `digicloud.db` and `.env`.
2. Keep the same `APP_SECRET_KEY`; changing it makes existing MFA secrets unreadable and invalidates sessions and trusted-device cookies.
3. Run `pip install -r requirements.txt`.
4. Start the application normally. SQLite Milestone 4 databases receive the required columns automatically.
5. Set the MFA policy under **Administration → Organizations**.

For PostgreSQL production deployments, create and review an Alembic migration rather than relying on automatic schema creation.
