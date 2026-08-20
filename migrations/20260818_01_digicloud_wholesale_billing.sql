ALTER TABLE digicloud_organization_settings
    ADD COLUMN IF NOT EXISTS platypus_billing_model VARCHAR(20) NOT NULL DEFAULT 'direct';

ALTER TABLE digicloud_organization_settings
    ADD COLUMN IF NOT EXISTS platypus_parent_customer_id VARCHAR(64) NOT NULL DEFAULT '';

ALTER TABLE digicloud_organization_settings
    ADD CONSTRAINT ck_digicloud_platypus_billing_model
    CHECK (platypus_billing_model IN ('direct', 'wholesale'));

CREATE TABLE IF NOT EXISTS digicloud_user_billing_links (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    domain_name VARCHAR(255) NOT NULL,
    username VARCHAR(32) NOT NULL,
    billing_model VARCHAR(20) NOT NULL DEFAULT 'direct',
    platypus_customer_id VARCHAR(64) NOT NULL,
    platypus_crid VARCHAR(64) NOT NULL DEFAULT '',
    platypus_service_data_id VARCHAR(64) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_digicloud_user_billing_link UNIQUE (domain_name, username)
);
CREATE INDEX IF NOT EXISTS ix_digicloud_user_billing_customer ON digicloud_user_billing_links (platypus_customer_id);
CREATE INDEX IF NOT EXISTS ix_digicloud_user_billing_status ON digicloud_user_billing_links (status);
