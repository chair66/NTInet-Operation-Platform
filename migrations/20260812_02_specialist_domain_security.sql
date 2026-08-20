-- Sprint 4.3.3c - per-user DigiCloud domain deny list
CREATE TABLE IF NOT EXISTS digicloud_user_hidden_domains (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_name VARCHAR(255) NOT NULL,
    created_by_user_id INTEGER NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_digicloud_user_hidden_domain UNIQUE (user_id, domain_name)
);
CREATE INDEX IF NOT EXISTS ix_digicloud_user_hidden_domains_user_id ON digicloud_user_hidden_domains(user_id);
CREATE INDEX IF NOT EXISTS ix_digicloud_user_hidden_domains_domain_name ON digicloud_user_hidden_domains(domain_name);
