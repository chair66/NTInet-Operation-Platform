# PLAT-003B.3 — User Editor and Lifecycle

Adds tenant-scoped user editing, administrative password resets, forced password changes, account unlock, MFA reset, one-time invitation links, and reversible soft deletion.

## Soft deletion
Deleted users retain their database identity and audit history. Authentication and normal user lists exclude them. Administrators can filter for deleted users and restore them.

## Invitations
Invitation tokens are stored only as SHA-256 hashes, expire after 48 hours, and are invalidated after use. This release generates a copyable link; outbound email delivery remains intentionally separate until an email provider is configured.

## Database
SQLite development databases are upgraded automatically at startup. PostgreSQL production deployments should add equivalent columns through Alembic before rollout.
