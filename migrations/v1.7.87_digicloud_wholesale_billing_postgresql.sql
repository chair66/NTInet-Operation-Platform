ALTER TABLE digicloud_organization_settings
    ADD COLUMN IF NOT EXISTS billing_model VARCHAR(20) NOT NULL DEFAULT 'direct',
    ADD COLUMN IF NOT EXISTS platypus_parent_customer_id VARCHAR(40) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS wholesale_rate_group_ids TEXT NOT NULL DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS default_wholesale_rate_group_id VARCHAR(20) NOT NULL DEFAULT '';
