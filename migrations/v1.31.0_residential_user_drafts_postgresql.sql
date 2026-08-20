CREATE TABLE IF NOT EXISTS digicloud_residential_user_drafts (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    domain_name VARCHAR(255) NOT NULL,
    extension VARCHAR(32) NOT NULL DEFAULT '',
    status VARCHAR(40) NOT NULL DEFAULT 'draft',
    user_data_json TEXT NOT NULL DEFAULT '{}',
    legacy_911_data_json TEXT NOT NULL DEFAULT '{}',
    legacy_911_status VARCHAR(40) NOT NULL DEFAULT 'not_validated',
    legacy_911_validation_json TEXT NOT NULL DEFAULT '{}',
    legacy_911_manual_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    last_error TEXT NOT NULL DEFAULT '',
    created_by_user_id INTEGER NULL REFERENCES users(id),
    updated_by_user_id INTEGER NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_organization_id ON digicloud_residential_user_drafts (organization_id);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_domain_name ON digicloud_residential_user_drafts (domain_name);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_extension ON digicloud_residential_user_drafts (extension);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_status ON digicloud_residential_user_drafts (status);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_legacy_911_status ON digicloud_residential_user_drafts (legacy_911_status);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_created_at ON digicloud_residential_user_drafts (created_at);
CREATE INDEX IF NOT EXISTS ix_digicloud_residential_user_drafts_updated_at ON digicloud_residential_user_drafts (updated_at);
