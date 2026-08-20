from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.core import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class CommunicationProfile(Base):
    __tablename__ = "communication_profiles"
    __table_args__ = (UniqueConstraint("organization_id", "channel", "name", name="uq_communication_profile_org_channel_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    module_slug: Mapped[str] = mapped_column(String(80), default="", index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(120))
    from_name: Mapped[str] = mapped_column(String(120), default="")
    sender_address: Mapped[str] = mapped_column(String(255), default="")
    reply_to: Mapped[str] = mapped_column(String(255), default="")
    smtp_host: Mapped[str] = mapped_column(String(255), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=465)
    smtp_username: Mapped[str] = mapped_column(String(255), default="")
    smtp_password_encrypted: Mapped[str] = mapped_column(Text, default="")
    smtp_security: Mapped[str] = mapped_column(String(20), default="ssl")
    inbound_email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    imap_host: Mapped[str] = mapped_column(String(255), default="")
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    imap_username: Mapped[str] = mapped_column(String(255), default="")
    imap_password_encrypted: Mapped[str] = mapped_column(Text, default="")
    imap_security: Mapped[str] = mapped_column(String(20), default="ssl")
    imap_folder: Mapped[str] = mapped_column(String(120), default="INBOX")
    imap_uidvalidity: Mapped[str] = mapped_column(String(80), default="")
    imap_last_uid: Mapped[int] = mapped_column(Integer, default=0)
    imap_last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imap_last_sync_status: Mapped[str] = mapped_column(String(30), default="not_synced")
    imap_last_sync_message: Mapped[str] = mapped_column(Text, default="")
    bandwidth_account_id: Mapped[str] = mapped_column(String(80), default="")
    bandwidth_auth_mode: Mapped[str] = mapped_column(String(30), default="oauth2_system")
    bandwidth_client_id: Mapped[str] = mapped_column(String(255), default="")
    bandwidth_client_secret_encrypted: Mapped[str] = mapped_column(Text, default="")
    bandwidth_token_url: Mapped[str] = mapped_column(String(255), default="https://api.bandwidth.com/api/v1/oauth2/token")
    bandwidth_username: Mapped[str] = mapped_column(String(255), default="")
    bandwidth_password_encrypted: Mapped[str] = mapped_column(Text, default="")
    bandwidth_application_id: Mapped[str] = mapped_column(String(120), default="")
    bandwidth_campaign_id: Mapped[str] = mapped_column(String(120), default="")
    bandwidth_api_base: Mapped[str] = mapped_column(String(255), default="https://messaging.bandwidth.com/api/v2")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_shareable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    daily_limit: Mapped[int] = mapped_column(Integer, default=0)
    last_test_status: Mapped[str] = mapped_column(String(20), default="not_tested")
    last_test_message: Mapped[str] = mapped_column(Text, default="")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_user_id], lazy="joined")

    @property
    def credential_configured(self) -> bool:
        if self.channel == "email":
            return bool(self.smtp_host and self.sender_address and (self.smtp_password_encrypted or not self.smtp_username))
        common = bool(self.bandwidth_account_id and self.bandwidth_application_id and self.sender_address)
        if self.bandwidth_auth_mode == "oauth2_system":
            return common
        if self.bandwidth_auth_mode == "oauth2_profile":
            return bool(common and self.bandwidth_client_id and self.bandwidth_client_secret_encrypted)
        return bool(common and self.bandwidth_username and self.bandwidth_password_encrypted)

    @property
    def inbound_email_configured(self) -> bool:
        return bool(self.channel == "email" and self.inbound_email_enabled and self.imap_host
                    and self.imap_username and self.imap_password_encrypted)
