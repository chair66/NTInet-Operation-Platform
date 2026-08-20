from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NOP - NTInet Operations Platform"
    app_env: str = "development"
    app_version: str = "1.8.16"
    app_secret_key: str = "change-me"
    database_url: str = "sqlite:///./digicloud.db"
    session_max_age_seconds: int = 28800
    bootstrap_admin_email: str = "admin@digicloud.local"
    bootstrap_admin_password: str = "ChangeMe123!"
    bootstrap_admin_name: str = "NTInet Administrator"
    mfa_issuer: str = "NTInet Operations"
    mfa_trusted_days: int = 30
    mfa_trusted_cookie_name: str = "digicloud_trusted_device"

    bandwidth_account_id: str
    bandwidth_client_id: str
    bandwidth_client_secret: str
    bandwidth_token_url: str = "https://api.bandwidth.com/api/v1/oauth2/token"
    bandwidth_api_base: str = "https://api.bandwidth.com/api/v2"

    netsapiens_api_url: str = ""
    netsapiens_token: str = ""
    # Reconcile NOP billing links with successful live DigiCloud user reads.
    # A user must be absent from at least two consecutive reads before NOP
    # flags the billing service for review.
    digicloud_user_reconcile_enabled: bool = True
    digicloud_user_reconcile_seconds: int = 900
    digicloud_user_reconcile_confirmations: int = 2

    # Plume read-only operator integration. The API base URL should include /api.
    plume_authorization_token_url: str = ""
    plume_authorization_header: str = ""
    plume_scope: str = ""
    plume_api_base_url: str = "https://piranha-gamma.prod.us-west-2.aws.plumenet.io/api"
    plume_reports_client_id: str = ""
    plume_token_refresh_grace_seconds: int = 60
    plume_device_days_offline: int = 30

    # Platypus 7 XML API (Sprint 4.4.0a)
    platypus_api_url: str = ""
    platypus_username: str = ""
    platypus_password: str = ""
    platypus_login_type: str = "staff"
    platypus_verify_ssl: bool = True
    platypus_timeout_seconds: int = 30
    # Sprint 4.4.0h: near-real-time discovery of customers created directly in Platypus.
    platypus_customer_watcher_enabled: bool = False
    platypus_customer_watcher_seconds: int = 300
    platypus_customer_watcher_statuses: str = "active,on_hold"
    platypus_customer_full_refresh_hours: int = 24

    request_timeout_seconds: int = 30
    provider_retry_attempts: int = 3
    provider_retry_backoff_seconds: float = 0.35
    api_log_limit: int = 250

    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_ssl: bool = True
    port_notification_email: str = ""
    bandwidth_port_webhook_token: str = ""

    # Ticketing / customer communications
    # These settings were present in the full ticketing stack but were omitted
    # from the consolidated Settings model during the Platypus merge.
    ticket_public_base_url: str = "http://127.0.0.1:8000"
    ticket_email_enabled: bool = True
    ticket_sms_enabled: bool = True
    ticket_communication_test_mode: bool = False
    ticket_auto_new_confirmation: bool = True
    ticket_auto_status_notifications: bool = True
    ticket_attachment_dir: str = "./data/ticket_attachments"
    ticket_attachment_max_bytes: int = 10 * 1024 * 1024
    user_signature_photo_dir: str = "./data/user_signatures"
    user_signature_photo_max_bytes: int = 2 * 1024 * 1024

    # Jobs / estimates settings used by the restored ticketing modules.
    app_timezone: str = "America/New_York"
    document_storage_dir: str = "./data/documents"
    job_scheduling_communications_enabled: bool = True
    job_appointment_email_enabled: bool = True
    job_appointment_sms_enabled: bool = True
    job_en_route_notification_enabled: bool = True
    job_reminder_hours: int = 24
    estimate_reminders_enabled: bool = True
    estimate_first_reminder_hours: int = 72
    estimate_second_reminder_hours: int = 48
    estimate_expiration_after_final_hours: int = 48

    oxio_env: str = "staging"
    oxio_staging_base_url: str = "https://api-staging.brandvno.com"
    oxio_production_base_url: str = "https://api.brandvno.com"
    oxio_api_key: str = ""
    oxio_api_secret: str = ""
    oxio_basic_auth: str = ""
    oxio_sim_inventory_path: str = ""
    oxio_sim_page_size: int = 500
    oxio_sim_page_size_parameter: str = "limit"

    model_config = SettingsConfigDict(
        env_file=(".env", "app/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
