# Core v1.1.3 – Data Cleanup

This release consolidates the staff organization records created by earlier development builds.

## Startup cleanup

- Selects the established `NTInet` organization as the canonical staff organization.
- Marks that organization as the single protected system organization.
- Removes the known empty legacy `NTInet Staff` / `digicloud` organization.
- Reassigns legacy audit and notification history to `NTInet` before removing the duplicate.
- Does not remove a legacy organization when it contains users.

## Protection behavior

Organization deletion now checks the `is_protected` database flag instead of treating every staff organization as protected. This allows normal staff-type organizations to be managed while preventing deletion of the canonical NTInet system organization.

## Database compatibility

Existing SQLite databases receive the new `organizations.is_protected` column automatically during startup.
