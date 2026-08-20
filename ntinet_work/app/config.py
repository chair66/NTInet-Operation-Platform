from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NTInet Operations"
    app_env: str = "development"
    app_version: str = "1.5.5"
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

    request_timeout_seconds: int = 30
    api_log_limit: int = 250

    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_ssl: bool = True
    port_notification_email: str = ""

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
