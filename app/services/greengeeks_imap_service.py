from __future__ import annotations

import imaplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.communication_models import CommunicationProfile
from app.services.communication_profile_service import CommunicationProfileService
from app.services.inbound_email_service import InboundEmailService


@dataclass(slots=True)
class GreenGeeksIMAPService:
    db: Session

    @staticmethod
    def _connect(profile: CommunicationProfile):
        context = ssl.create_default_context()
        if profile.imap_security == "ssl":
            client = imaplib.IMAP4_SSL(profile.imap_host, profile.imap_port, ssl_context=context, timeout=30)
        else:
            client = imaplib.IMAP4(profile.imap_host, profile.imap_port, timeout=30)
            if profile.imap_security == "starttls":
                client.starttls(ssl_context=context)
        client.login(profile.imap_username, CommunicationProfileService.imap_password(profile))
        return client

    def test_connection(self, profile: CommunicationProfile) -> str:
        if not profile.inbound_email_configured:
            raise RuntimeError("Inbound IMAP settings are incomplete.")
        client = self._connect(profile)
        try:
            status, _ = client.select(profile.imap_folder or "INBOX", readonly=True)
            if status != "OK":
                raise RuntimeError(f"Unable to open IMAP folder {profile.imap_folder or 'INBOX'}.")
            return f"IMAP authentication succeeded and {profile.imap_folder or 'INBOX'} is accessible."
        finally:
            try: client.logout()
            except imaplib.IMAP4.error: pass

    def sync_profile(self, profile: CommunicationProfile, limit: int = 100) -> dict[str, int]:
        if not profile.inbound_email_configured:
            raise RuntimeError("Inbound IMAP settings are incomplete.")
        counts = {"processed": 0, "unmatched": 0, "duplicate": 0, "failed": 0}
        client = self._connect(profile)
        try:
            status, _ = client.select(profile.imap_folder or "INBOX", readonly=True)
            if status != "OK": raise RuntimeError("Unable to open configured IMAP folder.")
            response = client.response("UIDVALIDITY")
            uidvalidity = ""
            if response and response[1]:
                raw = response[1][0] if isinstance(response[1], (list, tuple)) else response[1]
                uidvalidity = raw.decode() if isinstance(raw, bytes) else str(raw)
            if profile.imap_uidvalidity and uidvalidity and profile.imap_uidvalidity != uidvalidity:
                profile.imap_last_uid = 0
            profile.imap_uidvalidity = uidvalidity
            status, data = client.uid("search", None, f"UID {max(profile.imap_last_uid + 1, 1)}:*")
            if status != "OK": raise RuntimeError("IMAP UID search failed.")
            uids = [int(value) for value in (data[0] or b"").split()
                    if value and int(value) > int(profile.imap_last_uid or 0)]
            for uid in uids[:max(1, min(limit, 500))]:
                status, fetched = client.uid("fetch", str(uid), "(BODY.PEEK[])")
                if status != "OK":
                    counts["failed"] += 1; continue
                raw = next((item[1] for item in fetched if isinstance(item, tuple) and isinstance(item[1], bytes)), None)
                if raw is None:
                    counts["failed"] += 1; continue
                try:
                    with self.db.begin_nested():
                        imported = InboundEmailService(self.db).ingest_bytes(
                            profile, uidvalidity=uidvalidity, imap_uid=uid, raw_message=raw)
                        self.db.flush()
                    counts[imported.processing_status] = counts.get(imported.processing_status, 0) + 1
                    profile.imap_last_uid = max(profile.imap_last_uid, uid)
                except Exception as exc:
                    counts["failed"] += 1
                    profile.imap_last_sync_message = str(exc)[:2000]
            profile.imap_last_sync_at = datetime.now(timezone.utc)
            profile.imap_last_sync_status = "passed" if not counts["failed"] else "partial"
            profile.imap_last_sync_message = ", ".join(f"{value} {key}" for key, value in counts.items())
            return counts
        except Exception as exc:
            profile.imap_last_sync_at = datetime.now(timezone.utc)
            profile.imap_last_sync_status = "failed"
            profile.imap_last_sync_message = str(exc)[:2000]
            raise
        finally:
            try: client.logout()
            except imaplib.IMAP4.error: pass

    def sync_all(self) -> dict[int, dict[str, int]]:
        profiles = list(self.db.scalars(select(CommunicationProfile).where(
            CommunicationProfile.channel == "email",
            CommunicationProfile.is_active.is_(True),
            CommunicationProfile.inbound_email_enabled.is_(True),
        )).unique())
        results = {}
        for profile in profiles:
            try: results[profile.id] = self.sync_profile(profile)
            except Exception: results[profile.id] = {"failed": 1}
        return results
