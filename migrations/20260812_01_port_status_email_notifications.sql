-- Sprint 4.3.2h - Port Status Email Notifications
-- PostgreSQL migration. SQLite development databases self-upgrade in app/database/core.py.
ALTER TABLE port_drafts ADD COLUMN IF NOT EXISTS submitted_by_user_id INTEGER NULL REFERENCES users(id);
ALTER TABLE port_drafts ADD COLUMN IF NOT EXISTS notification_email VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE port_drafts ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE port_drafts ADD COLUMN IF NOT EXISTS notification_state_json TEXT NOT NULL DEFAULT '{}';
CREATE INDEX IF NOT EXISTS ix_port_drafts_submitted_by_user_id ON port_drafts (submitted_by_user_id);
