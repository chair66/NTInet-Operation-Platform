CREATE TABLE organizations (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(80) NOT NULL, 
	organization_type VARCHAR(30) NOT NULL, 
	active BOOLEAN NOT NULL, 
	is_protected BOOLEAN NOT NULL, 
	display_name VARCHAR(120), 
	status VARCHAR(20) NOT NULL, 
	notes TEXT NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	deleted_by_user_id INTEGER, 
	bandwidth_account_id VARCHAR(32), 
	bandwidth_site_ids TEXT NOT NULL, 
	mfa_policy VARCHAR(20) NOT NULL, 
	password_expiration_days INTEGER NOT NULL, 
	session_timeout_minutes INTEGER NOT NULL, 
	allow_api_access BOOLEAN NOT NULL, 
	timezone VARCHAR(64) NOT NULL, 
	date_format VARCHAR(20) NOT NULL, 
	default_role_id INTEGER, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_organizations_is_protected ON organizations (is_protected);

CREATE UNIQUE INDEX ix_organizations_name ON organizations (name);

CREATE INDEX ix_organizations_deleted_at ON organizations (deleted_at);

CREATE UNIQUE INDEX ix_organizations_slug ON organizations (slug);

CREATE INDEX ix_organizations_status ON organizations (status);

CREATE TABLE permissions (
	id SERIAL NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_permissions_key ON permissions (key);

CREATE TABLE roles (
	id SERIAL NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	organization_id INTEGER, 
	is_system BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_role_org_name UNIQUE (organization_id, name)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	active BOOLEAN NOT NULL, 
	is_superuser BOOLEAN NOT NULL, 
	organization_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_login_at TIMESTAMP WITH TIME ZONE, 
	mfa_enabled BOOLEAN NOT NULL, 
	mfa_required BOOLEAN NOT NULL, 
	mfa_secret_encrypted TEXT, 
	mfa_recovery_hashes TEXT NOT NULL, 
	mfa_enrolled_at TIMESTAMP WITH TIME ZONE, 
	force_password_change BOOLEAN NOT NULL, 
	password_changed_at TIMESTAMP WITH TIME ZONE, 
	locked_at TIMESTAMP WITH TIME ZONE, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	deleted_by_user_id INTEGER, 
	invitation_token_hash VARCHAR(64), 
	invitation_expires_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_deleted_at ON users (deleted_at);

CREATE INDEX ix_users_invitation_token_hash ON users (invitation_token_hash);

CREATE TABLE mobile_plans (
	id SERIAL NOT NULL, 
	plan_code VARCHAR(40) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT NOT NULL, 
	data_gb INTEGER NOT NULL, 
	monthly_price NUMERIC(10, 2) NOT NULL, 
	top_up_price_per_gb NUMERIC(10, 2) NOT NULL, 
	unlimited_talk_text BOOLEAN NOT NULL, 
	active BOOLEAN NOT NULL, 
	provider_plan_id VARCHAR(120), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_mobile_plans_provider_plan_id ON mobile_plans (provider_plan_id);

CREATE INDEX ix_mobile_plans_created_at ON mobile_plans (created_at);

CREATE INDEX ix_mobile_plans_name ON mobile_plans (name);

CREATE INDEX ix_mobile_plans_active ON mobile_plans (active);

CREATE UNIQUE INDEX ix_mobile_plans_plan_code ON mobile_plans (plan_code);

CREATE INDEX ix_mobile_plans_updated_at ON mobile_plans (updated_at);

CREATE TABLE mobile_sync_states (
	id SERIAL NOT NULL, 
	provider VARCHAR(60) NOT NULL, 
	last_attempt_at TIMESTAMP WITH TIME ZONE, 
	last_success_at TIMESTAMP WITH TIME ZONE, 
	records_received INTEGER NOT NULL, 
	last_error TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_mobile_sync_states_provider ON mobile_sync_states (provider);

CREATE TABLE user_roles (
	user_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, role_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
);

CREATE TABLE role_permissions (
	role_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);

CREATE TABLE organization_modules (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	module_slug VARCHAR(80) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_organization_module_slug UNIQUE (organization_id, module_slug), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
);

CREATE INDEX ix_organization_modules_module_slug ON organization_modules (module_slug);

CREATE INDEX ix_organization_modules_organization_id ON organization_modules (organization_id);

CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	user_id INTEGER, 
	organization_id INTEGER, 
	action VARCHAR(100) NOT NULL, 
	resource_type VARCHAR(80) NOT NULL, 
	resource_id VARCHAR(160) NOT NULL, 
	detail TEXT NOT NULL, 
	module VARCHAR(80) NOT NULL, 
	event_data TEXT NOT NULL, 
	ip_address VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

CREATE INDEX ix_audit_logs_module ON audit_logs (module);

CREATE TABLE notification_events (
	id SERIAL NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	organization_id INTEGER, 
	actor_user_id INTEGER, 
	recipient_user_id INTEGER, 
	event_type VARCHAR(100) NOT NULL, 
	channel VARCHAR(30) NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	payload TEXT NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	processed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(actor_user_id) REFERENCES users (id), 
	FOREIGN KEY(recipient_user_id) REFERENCES users (id)
);

CREATE INDEX ix_notification_events_created_at ON notification_events (created_at);

CREATE INDEX ix_notification_events_organization_id ON notification_events (organization_id);

CREATE INDEX ix_notification_events_recipient_user_id ON notification_events (recipient_user_id);

CREATE INDEX ix_notification_events_status ON notification_events (status);

CREATE INDEX ix_notification_events_event_type ON notification_events (event_type);

CREATE TABLE trusted_devices (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	device_name VARCHAR(160) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_used_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	ip_address VARCHAR(64) NOT NULL, 
	user_agent VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_trusted_devices_user_id ON trusted_devices (user_id);

CREATE UNIQUE INDEX ix_trusted_devices_token_hash ON trusted_devices (token_hash);

CREATE INDEX ix_trusted_devices_expires_at ON trusted_devices (expires_at);

CREATE TABLE port_drafts (
	id VARCHAR(36) NOT NULL, 
	nti_reference VARCHAR(32) NOT NULL, 
	organization_id INTEGER NOT NULL, 
	created_by_user_id INTEGER NOT NULL, 
	assigned_to_user_id INTEGER, 
	status VARCHAR(32) NOT NULL, 
	customer_name VARCHAR(120) NOT NULL, 
	billing_telephone_number VARCHAR(32) NOT NULL, 
	losing_carrier_name VARCHAR(120) NOT NULL, 
	payload_json TEXT NOT NULL, 
	bandwidth_order_id VARCHAR(80), 
	bandwidth_status VARCHAR(40) NOT NULL, 
	last_error_code VARCHAR(40) NOT NULL, 
	last_error_message TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_to_user_id) REFERENCES users (id)
);

CREATE INDEX ix_port_drafts_created_by_user_id ON port_drafts (created_by_user_id);

CREATE INDEX ix_port_drafts_created_at ON port_drafts (created_at);

CREATE INDEX ix_port_drafts_updated_at ON port_drafts (updated_at);

CREATE INDEX ix_port_drafts_status ON port_drafts (status);

CREATE INDEX ix_port_drafts_bandwidth_order_id ON port_drafts (bandwidth_order_id);

CREATE UNIQUE INDEX ix_port_drafts_nti_reference ON port_drafts (nti_reference);

CREATE INDEX ix_port_drafts_customer_name ON port_drafts (customer_name);

CREATE INDEX ix_port_drafts_assigned_to_user_id ON port_drafts (assigned_to_user_id);

CREATE INDEX ix_port_drafts_billing_telephone_number ON port_drafts (billing_telephone_number);

CREATE INDEX ix_port_drafts_organization_id ON port_drafts (organization_id);

CREATE TABLE digicloud_organization_settings (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	netsapiens_reseller VARCHAR(120) NOT NULL, 
	default_area_code VARCHAR(10) NOT NULL, 
	default_time_zone VARCHAR(64) NOT NULL, 
	default_max_calls INTEGER NOT NULL, 
	default_max_offnet_calls INTEGER NOT NULL, 
	default_recording_enabled BOOLEAN NOT NULL, 
	default_transcription_enabled BOOLEAN NOT NULL, 
	default_transcription_provider VARCHAR(40) NOT NULL, 
	default_email_from VARCHAR(255) NOT NULL, 
	provisioning_server VARCHAR(255) NOT NULL, 
	active BOOLEAN NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_by_user_id INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_digicloud_settings_org UNIQUE (organization_id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_digicloud_organization_settings_organization_id ON digicloud_organization_settings (organization_id);

CREATE TABLE digicloud_domains (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	domain_name VARCHAR(255) NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	caller_id_name VARCHAR(120) NOT NULL, 
	caller_id_number VARCHAR(32) NOT NULL, 
	emergency_caller_id VARCHAR(32) NOT NULL, 
	area_code VARCHAR(10) NOT NULL, 
	time_zone VARCHAR(64) NOT NULL, 
	max_calls INTEGER NOT NULL, 
	max_offnet_calls INTEGER NOT NULL, 
	recording_enabled BOOLEAN NOT NULL, 
	transcription_enabled BOOLEAN NOT NULL, 
	transcription_provider VARCHAR(40) NOT NULL, 
	email_from VARCHAR(255) NOT NULL, 
	provider_domain_id VARCHAR(255) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	last_error TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_digicloud_domain_name UNIQUE (domain_name), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE INDEX ix_digicloud_domains_status ON digicloud_domains (status);

CREATE INDEX ix_digicloud_domains_organization_id ON digicloud_domains (organization_id);

CREATE INDEX ix_digicloud_domains_created_at ON digicloud_domains (created_at);

CREATE INDEX ix_digicloud_domains_domain_name ON digicloud_domains (domain_name);

CREATE INDEX ix_digicloud_domains_deleted_at ON digicloud_domains (deleted_at);

CREATE TABLE digicloud_managed_user_domains (
	id SERIAL NOT NULL, 
	domain_name VARCHAR(255) NOT NULL, 
	organization_id INTEGER NOT NULL, 
	user_management_enabled BOOLEAN NOT NULL, 
	active BOOLEAN NOT NULL, 
	notes TEXT NOT NULL, 
	approved_by_user_id INTEGER, 
	approved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_digicloud_managed_user_domain UNIQUE (domain_name), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(approved_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_digicloud_managed_user_domains_organization_id ON digicloud_managed_user_domains (organization_id);

CREATE INDEX ix_digicloud_managed_user_domains_user_management_enabled ON digicloud_managed_user_domains (user_management_enabled);

CREATE UNIQUE INDEX ix_digicloud_managed_user_domains_domain_name ON digicloud_managed_user_domains (domain_name);

CREATE INDEX ix_digicloud_managed_user_domains_active ON digicloud_managed_user_domains (active);

CREATE TABLE digicloud_reseller_device_models (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	model_name VARCHAR(160) NOT NULL, 
	api_model_value VARCHAR(120) NOT NULL, 
	brand VARCHAR(80) NOT NULL, 
	device_type VARCHAR(40) NOT NULL, 
	config_format VARCHAR(80) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	is_default BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_digicloud_reseller_device_model UNIQUE (organization_id, model_name), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id) ON DELETE CASCADE
);

CREATE INDEX ix_digicloud_reseller_device_models_brand ON digicloud_reseller_device_models (brand);

CREATE INDEX ix_digicloud_reseller_device_models_model_name ON digicloud_reseller_device_models (model_name);

CREATE INDEX ix_digicloud_reseller_device_models_api_model_value ON digicloud_reseller_device_models (api_model_value);

CREATE INDEX ix_digicloud_reseller_device_models_enabled ON digicloud_reseller_device_models (enabled);

CREATE INDEX ix_digicloud_reseller_device_models_organization_id ON digicloud_reseller_device_models (organization_id);

CREATE TABLE mobile_customers (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	customer_number VARCHAR(32) NOT NULL, 
	customer_type VARCHAR(20) NOT NULL, 
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	business_name VARCHAR(160) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(32) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	provider_customer_id VARCHAR(120), 
	notes TEXT NOT NULL, 
	created_by_user_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_mobile_customers_customer_number ON mobile_customers (customer_number);

CREATE INDEX ix_mobile_customers_customer_type ON mobile_customers (customer_type);

CREATE INDEX ix_mobile_customers_organization_id ON mobile_customers (organization_id);

CREATE INDEX ix_mobile_customers_updated_at ON mobile_customers (updated_at);

CREATE INDEX ix_mobile_customers_provider_customer_id ON mobile_customers (provider_customer_id);

CREATE INDEX ix_mobile_customers_created_at ON mobile_customers (created_at);

CREATE INDEX ix_mobile_customers_status ON mobile_customers (status);

CREATE INDEX ix_mobile_customers_email ON mobile_customers (email);

CREATE TABLE mobile_exceptions (
	id SERIAL NOT NULL, 
	exception_type VARCHAR(50) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	detail TEXT NOT NULL, 
	resource_type VARCHAR(50) NOT NULL, 
	resource_id VARCHAR(80) NOT NULL, 
	assigned_to_user_id INTEGER, 
	resolved_by_user_id INTEGER, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assigned_to_user_id) REFERENCES users (id), 
	FOREIGN KEY(resolved_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_mobile_exceptions_severity ON mobile_exceptions (severity);

CREATE INDEX ix_mobile_exceptions_status ON mobile_exceptions (status);

CREATE INDEX ix_mobile_exceptions_assigned_to_user_id ON mobile_exceptions (assigned_to_user_id);

CREATE INDEX ix_mobile_exceptions_created_at ON mobile_exceptions (created_at);

CREATE INDEX ix_mobile_exceptions_exception_type ON mobile_exceptions (exception_type);

CREATE INDEX ix_mobile_exceptions_updated_at ON mobile_exceptions (updated_at);

CREATE TABLE port_submission_attempts (
	id SERIAL NOT NULL, 
	draft_id VARCHAR(36) NOT NULL, 
	attempt_number INTEGER NOT NULL, 
	submitted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	success BOOLEAN NOT NULL, 
	request_json TEXT NOT NULL, 
	response_json TEXT NOT NULL, 
	error_code VARCHAR(40) NOT NULL, 
	error_message TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(draft_id) REFERENCES port_drafts (id) ON DELETE CASCADE
);

CREATE INDEX ix_port_submission_attempts_draft_id ON port_submission_attempts (draft_id);

CREATE INDEX ix_port_submission_attempts_submitted_at ON port_submission_attempts (submitted_at);

CREATE TABLE port_draft_revisions (
	id SERIAL NOT NULL, 
	draft_id VARCHAR(36) NOT NULL, 
	revision_number INTEGER NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	summary VARCHAR(255) NOT NULL, 
	payload_json TEXT NOT NULL, 
	created_by_user_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(draft_id) REFERENCES port_drafts (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_port_draft_revisions_event_type ON port_draft_revisions (event_type);

CREATE INDEX ix_port_draft_revisions_draft_id ON port_draft_revisions (draft_id);

CREATE INDEX ix_port_draft_revisions_created_at ON port_draft_revisions (created_at);

CREATE TABLE port_timeline_events (
	id SERIAL NOT NULL, 
	draft_id VARCHAR(36) NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	detail TEXT NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	event_data_json TEXT NOT NULL, 
	created_by_user_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(draft_id) REFERENCES port_drafts (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_port_timeline_events_draft_id ON port_timeline_events (draft_id);

CREATE INDEX ix_port_timeline_events_created_at ON port_timeline_events (created_at);

CREATE INDEX ix_port_timeline_events_event_type ON port_timeline_events (event_type);

CREATE TABLE portability_snapshots (
	id SERIAL NOT NULL, 
	draft_id VARCHAR(36) NOT NULL, 
	raw_response_json TEXT NOT NULL, 
	summary_json TEXT NOT NULL, 
	changed BOOLEAN NOT NULL, 
	change_summary TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(draft_id) REFERENCES port_drafts (id) ON DELETE CASCADE
);

CREATE INDEX ix_portability_snapshots_draft_id ON portability_snapshots (draft_id);

CREATE INDEX ix_portability_snapshots_created_at ON portability_snapshots (created_at);

CREATE TABLE digicloud_phone_numbers (
	id SERIAL NOT NULL, 
	organization_id INTEGER NOT NULL, 
	telephone_number VARCHAR(32) NOT NULL, 
	domain_id INTEGER, 
	status VARCHAR(30) NOT NULL, 
	notes TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_digicloud_phone_number UNIQUE (telephone_number), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(domain_id) REFERENCES digicloud_domains (id)
);

CREATE INDEX ix_digicloud_phone_numbers_telephone_number ON digicloud_phone_numbers (telephone_number);

CREATE INDEX ix_digicloud_phone_numbers_domain_id ON digicloud_phone_numbers (domain_id);

CREATE INDEX ix_digicloud_phone_numbers_organization_id ON digicloud_phone_numbers (organization_id);

CREATE INDEX ix_digicloud_phone_numbers_status ON digicloud_phone_numbers (status);

CREATE TABLE mobile_sims (
	id SERIAL NOT NULL, 
	iccid VARCHAR(32) NOT NULL, 
	sim_type VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	eid VARCHAR(40) NOT NULL, 
	provider VARCHAR(60) NOT NULL, 
	provider_sim_id VARCHAR(120), 
	activation_code TEXT NOT NULL, 
	assigned_customer_id INTEGER, 
	notes TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assigned_customer_id) REFERENCES mobile_customers (id)
);

CREATE UNIQUE INDEX ix_mobile_sims_iccid ON mobile_sims (iccid);

CREATE INDEX ix_mobile_sims_eid ON mobile_sims (eid);

CREATE INDEX ix_mobile_sims_created_at ON mobile_sims (created_at);

CREATE INDEX ix_mobile_sims_assigned_customer_id ON mobile_sims (assigned_customer_id);

CREATE INDEX ix_mobile_sims_updated_at ON mobile_sims (updated_at);

CREATE INDEX ix_mobile_sims_status ON mobile_sims (status);

CREATE INDEX ix_mobile_sims_sim_type ON mobile_sims (sim_type);

CREATE INDEX ix_mobile_sims_provider_sim_id ON mobile_sims (provider_sim_id);

CREATE TABLE mobile_orders (
	id SERIAL NOT NULL, 
	order_number VARCHAR(40) NOT NULL, 
	customer_id INTEGER, 
	order_type VARCHAR(40) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	assigned_to_user_id INTEGER, 
	provider_order_id VARCHAR(120), 
	payload_json TEXT NOT NULL, 
	last_error TEXT NOT NULL, 
	created_by_user_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES mobile_customers (id), 
	FOREIGN KEY(assigned_to_user_id) REFERENCES users (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_mobile_orders_provider_order_id ON mobile_orders (provider_order_id);

CREATE INDEX ix_mobile_orders_customer_id ON mobile_orders (customer_id);

CREATE UNIQUE INDEX ix_mobile_orders_order_number ON mobile_orders (order_number);

CREATE INDEX ix_mobile_orders_status ON mobile_orders (status);

CREATE INDEX ix_mobile_orders_created_at ON mobile_orders (created_at);

CREATE INDEX ix_mobile_orders_assigned_to_user_id ON mobile_orders (assigned_to_user_id);

CREATE INDEX ix_mobile_orders_updated_at ON mobile_orders (updated_at);

CREATE INDEX ix_mobile_orders_order_type ON mobile_orders (order_type);

CREATE TABLE mobile_lines (
	id SERIAL NOT NULL, 
	customer_id INTEGER NOT NULL, 
	plan_id INTEGER, 
	sim_id INTEGER, 
	mobile_number VARCHAR(32) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	activation_type VARCHAR(30) NOT NULL, 
	provider_line_id VARCHAR(120), 
	activated_at TIMESTAMP WITH TIME ZONE, 
	suspended_at TIMESTAMP WITH TIME ZONE, 
	disconnected_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES mobile_customers (id), 
	FOREIGN KEY(plan_id) REFERENCES mobile_plans (id), 
	FOREIGN KEY(sim_id) REFERENCES mobile_sims (id)
);

CREATE INDEX ix_mobile_lines_customer_id ON mobile_lines (customer_id);

CREATE INDEX ix_mobile_lines_status ON mobile_lines (status);

CREATE INDEX ix_mobile_lines_mobile_number ON mobile_lines (mobile_number);

CREATE INDEX ix_mobile_lines_created_at ON mobile_lines (created_at);

CREATE UNIQUE INDEX ix_mobile_lines_sim_id ON mobile_lines (sim_id);

CREATE INDEX ix_mobile_lines_updated_at ON mobile_lines (updated_at);

CREATE INDEX ix_mobile_lines_plan_id ON mobile_lines (plan_id);

CREATE INDEX ix_mobile_lines_provider_line_id ON mobile_lines (provider_line_id);

CREATE TABLE mobile_port_requests (
	id SERIAL NOT NULL, 
	port_number VARCHAR(40) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	order_id INTEGER, 
	telephone_number VARCHAR(32) NOT NULL, 
	losing_carrier VARCHAR(120) NOT NULL, 
	account_number VARCHAR(80) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	requested_foc_at TIMESTAMP WITH TIME ZONE, 
	confirmed_foc_at TIMESTAMP WITH TIME ZONE, 
	provider_port_id VARCHAR(120), 
	last_error TEXT NOT NULL, 
	created_by_user_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES mobile_customers (id), 
	FOREIGN KEY(order_id) REFERENCES mobile_orders (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_mobile_port_requests_telephone_number ON mobile_port_requests (telephone_number);

CREATE INDEX ix_mobile_port_requests_created_at ON mobile_port_requests (created_at);

CREATE INDEX ix_mobile_port_requests_order_id ON mobile_port_requests (order_id);

CREATE UNIQUE INDEX ix_mobile_port_requests_port_number ON mobile_port_requests (port_number);

CREATE INDEX ix_mobile_port_requests_customer_id ON mobile_port_requests (customer_id);

CREATE INDEX ix_mobile_port_requests_provider_port_id ON mobile_port_requests (provider_port_id);

CREATE INDEX ix_mobile_port_requests_status ON mobile_port_requests (status);

CREATE INDEX ix_mobile_port_requests_updated_at ON mobile_port_requests (updated_at);

ALTER TABLE users ADD FOREIGN KEY(deleted_by_user_id) REFERENCES users (id);

ALTER TABLE users ADD FOREIGN KEY(organization_id) REFERENCES organizations (id);

ALTER TABLE roles ADD FOREIGN KEY(organization_id) REFERENCES organizations (id);

ALTER TABLE organizations ADD FOREIGN KEY(deleted_by_user_id) REFERENCES users (id);

ALTER TABLE organizations ADD FOREIGN KEY(default_role_id) REFERENCES roles (id);
