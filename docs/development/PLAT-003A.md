# PLAT-003A — My Account

Adds a self-service account center for every authenticated user.

## Included

- My Account overview at `/account`
- Edit full name and sign-in email
- Duplicate-email protection
- Change password with current-password verification
- Minimum 12-character password policy
- MFA status and setup link
- Recovery-code regeneration
- MFA disable with password confirmation when organization policy permits
- Trusted-browser review and revocation
- Recent account activity
- Audit logging for profile, password, and MFA changes

## Security notes

All account operations use the authenticated user ID from the server-side request context. No user ID is accepted from forms or URLs. Trusted-device revocation verifies ownership. MFA cannot be disabled when required by the user or organization.

Cookie sessions do not currently support a reliable "log out all sessions" feature. That capability requires server-side session storage and is intentionally deferred.
