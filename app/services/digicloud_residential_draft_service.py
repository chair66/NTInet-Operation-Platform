from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import DigiCloudResidentialUserDraft


class DigiCloudResidentialDraftService:
    """Persistence for residential DigiCloud user provisioning drafts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _loads(value: str) -> dict[str, Any]:
        try:
            parsed = json.loads(value or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}

    @staticmethod
    def view(draft: DigiCloudResidentialUserDraft | None) -> dict[str, Any] | None:
        if draft is None:
            return None
        return {
            "id": draft.id,
            "organization_id": draft.organization_id,
            "domain_name": draft.domain_name,
            "extension": draft.extension,
            "status": draft.status,
            "user_data": DigiCloudResidentialDraftService._loads(draft.user_data_json),
            "legacy_911": DigiCloudResidentialDraftService._loads(draft.legacy_911_data_json),
            "validation": DigiCloudResidentialDraftService._loads(draft.legacy_911_validation_json),
            "legacy_911_status": draft.legacy_911_status,
            "legacy_911_manual_confirmed": draft.legacy_911_manual_confirmed,
            "last_error": draft.last_error,
            "created_at": draft.created_at,
            "updated_at": draft.updated_at,
            "completed_at": draft.completed_at,
        }

    def get(self, draft_id: int, organization_id: int, domain_name: str) -> DigiCloudResidentialUserDraft | None:
        return self.db.scalar(
            select(DigiCloudResidentialUserDraft).where(
                DigiCloudResidentialUserDraft.id == draft_id,
                DigiCloudResidentialUserDraft.organization_id == organization_id,
                DigiCloudResidentialUserDraft.domain_name == domain_name,
            )
        )

    def pending(self, organization_id: int, domain_name: str) -> list[DigiCloudResidentialUserDraft]:
        return list(self.db.scalars(
            select(DigiCloudResidentialUserDraft)
            .where(
                DigiCloudResidentialUserDraft.organization_id == organization_id,
                DigiCloudResidentialUserDraft.domain_name == domain_name,
                DigiCloudResidentialUserDraft.status != "completed",
            )
            .order_by(DigiCloudResidentialUserDraft.updated_at.desc())
        ))

    def save(
        self,
        *,
        organization_id: int,
        domain_name: str,
        extension: str,
        user_data: dict[str, Any],
        legacy_911: dict[str, Any],
        actor_user_id: int | None,
        draft_id: int | None = None,
        status: str = "draft",
        legacy_911_status: str = "not_validated",
        validation: dict[str, Any] | None = None,
        last_error: str = "",
        manual_confirmed: bool = False,
    ) -> DigiCloudResidentialUserDraft:
        draft = self.get(draft_id, organization_id, domain_name) if draft_id else None
        if draft is None:
            draft = DigiCloudResidentialUserDraft(
                organization_id=organization_id,
                domain_name=domain_name,
                created_by_user_id=actor_user_id,
            )
            self.db.add(draft)
        draft.extension = extension
        draft.status = status
        draft.user_data_json = json.dumps(user_data, sort_keys=True)
        draft.legacy_911_data_json = json.dumps(legacy_911, sort_keys=True)
        draft.legacy_911_status = legacy_911_status
        draft.legacy_911_validation_json = json.dumps(validation or {}, sort_keys=True, default=str)
        draft.legacy_911_manual_confirmed = bool(manual_confirmed)
        draft.last_error = last_error
        draft.updated_by_user_id = actor_user_id
        draft.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return draft

    def complete(self, draft: DigiCloudResidentialUserDraft) -> None:
        draft.status = "completed"
        draft.legacy_911_status = "confirmed"
        draft.last_error = ""
        draft.completed_at = datetime.now(timezone.utc)
        draft.updated_at = datetime.now(timezone.utc)
        self.db.flush()
