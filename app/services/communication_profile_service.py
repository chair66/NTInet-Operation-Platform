from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.database.communication_models import CommunicationProfile
from app.database.models import Organization
from app.database.ticket_models import Ticket
from app.security.context import SecurityContext
from app.security.mfa import decrypt_secret, encrypt_secret

CHANNELS = {"email", "sms"}
PROVIDERS = {"email": "smtp", "sms": "bandwidth"}

@dataclass(slots=True)
class CommunicationProfileService:
    db: Session
    context: SecurityContext | None = None

    def manageable(self):
        stmt = select(CommunicationProfile)
        if self.context and not self.context.is_staff:
            stmt = stmt.where(CommunicationProfile.organization_id == self.context.organization_id)
        return list(self.db.scalars(stmt.order_by(CommunicationProfile.organization_id, CommunicationProfile.channel, CommunicationProfile.name)).unique())

    def available(self, organization_id: int, channel: str | None = None):
        stmt = select(CommunicationProfile).join(Organization).where(
            CommunicationProfile.is_active.is_(True),
            or_(CommunicationProfile.organization_id == organization_id,
                (Organization.organization_type == "staff") & CommunicationProfile.is_shareable.is_(True)))
        if channel: stmt = stmt.where(CommunicationProfile.channel == channel)
        return list(self.db.scalars(stmt.order_by(CommunicationProfile.organization_id != organization_id, CommunicationProfile.name)).unique())

    def get_manageable(self, profile_id: int):
        profile = self.db.get(CommunicationProfile, profile_id)
        if not profile or (self.context and not self.context.is_staff and profile.organization_id != self.context.organization_id):
            return None
        return profile

    def save(self, profile: CommunicationProfile | None, *, organization_id: int, channel: str,
             name: str, module_slug: str, from_name: str, sender_address: str, reply_to: str,
             smtp_host: str, smtp_port: int, smtp_username: str, smtp_password: str,
             smtp_security: str, bandwidth_account_id: str, bandwidth_username: str,
             bandwidth_password: str, bandwidth_application_id: str, bandwidth_campaign_id: str,
             bandwidth_api_base: str, bandwidth_auth_mode: str = "oauth2_system",
             bandwidth_client_id: str = "", bandwidth_client_secret: str = "",
             bandwidth_token_url: str = "https://api.bandwidth.com/api/v1/oauth2/token",
             inbound_email_enabled: bool = False, imap_host: str = "", imap_port: int = 993,
             imap_username: str = "", imap_password: str = "", imap_security: str = "ssl",
             imap_folder: str = "INBOX",
             is_default: bool = False, is_active: bool = True, is_shareable: bool = False,
             daily_limit: int = 0, actor_user_id: int = 0) -> CommunicationProfile:
        if channel not in CHANNELS or not name.strip(): raise ValueError("Profile name and valid channel are required.")
        if self.context and not self.context.is_staff:
            organization_id = self.context.organization_id; is_shareable = False
        if profile is None:
            profile = CommunicationProfile(organization_id=organization_id, channel=channel,
                provider=PROVIDERS[channel], name=name.strip(), created_by_user_id=actor_user_id)
            self.db.add(profile)
        elif profile.channel != channel:
            raise ValueError("A profile channel cannot be changed after creation.")
        profile.organization_id=organization_id; profile.name=name.strip(); profile.module_slug=module_slug.strip()
        profile.from_name=from_name.strip(); profile.sender_address=sender_address.strip(); profile.reply_to=reply_to.strip()
        profile.smtp_host=smtp_host.strip(); profile.smtp_port=max(1,min(int(smtp_port),65535)); profile.smtp_username=smtp_username.strip()
        if smtp_password.strip(): profile.smtp_password_encrypted=encrypt_secret(smtp_password.strip())
        profile.smtp_security=smtp_security if smtp_security in {"ssl","starttls","none"} else "ssl"
        profile.inbound_email_enabled=bool(channel == "email" and inbound_email_enabled)
        profile.imap_host=imap_host.strip(); profile.imap_port=max(1,min(int(imap_port),65535))
        profile.imap_username=imap_username.strip()
        if imap_password.strip(): profile.imap_password_encrypted=encrypt_secret(imap_password.strip())
        profile.imap_security=imap_security if imap_security in {"ssl","starttls","none"} else "ssl"
        profile.imap_folder=imap_folder.strip() or "INBOX"
        profile.bandwidth_account_id=bandwidth_account_id.strip(); profile.bandwidth_username=bandwidth_username.strip()
        if bandwidth_password.strip(): profile.bandwidth_password_encrypted=encrypt_secret(bandwidth_password.strip())
        if bandwidth_auth_mode not in {"oauth2_system", "oauth2_profile", "basic"}:
            raise ValueError("Invalid Bandwidth authentication mode.")
        organization = self.db.get(Organization, organization_id)
        if bandwidth_auth_mode == "oauth2_system" and organization and not organization.is_staff:
            raise ValueError("Reseller-owned profiles must use profile OAuth credentials or legacy Basic authentication.")
        profile.bandwidth_auth_mode = bandwidth_auth_mode
        profile.bandwidth_client_id = bandwidth_client_id.strip()
        if bandwidth_client_secret.strip():
            profile.bandwidth_client_secret_encrypted = encrypt_secret(bandwidth_client_secret.strip())
        profile.bandwidth_token_url = bandwidth_token_url.strip() or "https://api.bandwidth.com/api/v1/oauth2/token"
        profile.bandwidth_application_id=bandwidth_application_id.strip(); profile.bandwidth_campaign_id=bandwidth_campaign_id.strip()
        profile.bandwidth_api_base=bandwidth_api_base.strip() or "https://messaging.bandwidth.com/api/v2"
        profile.is_default=is_default; profile.is_active=is_active; profile.is_shareable=is_shareable
        profile.daily_limit=max(0,int(daily_limit)); profile.updated_by_user_id=actor_user_id
        self.db.flush()
        if is_default:
            for other in self.db.scalars(select(CommunicationProfile).where(
                CommunicationProfile.organization_id==profile.organization_id,
                CommunicationProfile.channel==profile.channel,
                CommunicationProfile.module_slug==profile.module_slug,
                CommunicationProfile.id!=profile.id)):
                other.is_default=False
        return profile

    def resolve(self, ticket: Ticket, channel: str) -> CommunicationProfile | None:
        explicit_id = ticket.email_profile_id if channel == "email" else ticket.sms_profile_id
        available = self.available(ticket.owning_organization_id, channel)
        if explicit_id:
            explicit = next((p for p in available if p.id == explicit_id), None)
            if explicit: return explicit
        for profile in available:
            if profile.organization_id == ticket.owning_organization_id and profile.module_slug == "support-tickets" and profile.is_default: return profile
        for profile in available:
            if profile.organization_id == ticket.owning_organization_id and not profile.module_slug and profile.is_default: return profile
        for profile in available:
            if profile.organization_id != ticket.owning_organization_id and profile.module_slug == "support-tickets" and profile.is_default: return profile
        for profile in available:
            if profile.organization_id != ticket.owning_organization_id and not profile.module_slug and profile.is_default: return profile
        return None

    def resolve_for_organization(self, organization_id: int, channel: str,
                                 module_slug: str = "customer-management") -> CommunicationProfile | None:
        available = self.available(organization_id, channel)
        for owner_id, module in (
            (organization_id, module_slug), (organization_id, ""),
            (organization_id, "support-tickets"),
        ):
            match = next((p for p in available if p.organization_id == owner_id
                          and p.module_slug == module and p.is_default), None)
            if match:
                return match
        for module in (module_slug, "", "support-tickets"):
            match = next((p for p in available if p.organization_id != organization_id
                          and p.module_slug == module and p.is_default), None)
            if match:
                return match
        return None

    @staticmethod
    def password(profile: CommunicationProfile) -> str:
        encrypted = profile.smtp_password_encrypted if profile.channel == "email" else profile.bandwidth_password_encrypted
        return decrypt_secret(encrypted) if encrypted else ""

    @staticmethod
    def client_secret(profile: CommunicationProfile) -> str:
        return decrypt_secret(profile.bandwidth_client_secret_encrypted) if profile.bandwidth_client_secret_encrypted else ""

    @staticmethod
    def imap_password(profile: CommunicationProfile) -> str:
        return decrypt_secret(profile.imap_password_encrypted) if profile.imap_password_encrypted else ""

    def mark_test(self, profile: CommunicationProfile, ok: bool, message: str) -> None:
        profile.last_test_status="passed" if ok else "failed"; profile.last_test_message=message[:2000]
        profile.last_tested_at=datetime.now(timezone.utc)
