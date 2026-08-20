from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.mobile_models import MobileSIM, MobileSyncState
from app.providers.mobile.client import BrandVNOClient
from app.providers.mobile.exceptions import MobileProviderRequestError


@dataclass(slots=True)
class InventoryRefreshResult:
    imported: int = 0
    updated: int = 0
    unchanged: int = 0
    received: int = 0
    refreshed_at: datetime | None = None


class SIMInventoryService:
    def __init__(self, client: BrandVNOClient | None = None) -> None:
        self.client = client or BrandVNOClient()
        self.settings = get_settings()

    async def fetch(self) -> list[dict[str, Any]]:
        payload = await self.client.get_json(
            self.settings.oxio_sim_inventory_path,
            params=self._request_params(),
        )
        records = self._extract_records(payload)
        if not records and payload not in ([], {}, None):
            raise MobileProviderRequestError(
                "BrandVNO responded successfully, but the SIM list could not be "
                "identified in the response. The configured endpoint or response "
                "mapping may need adjustment."
            )
        return records

    async def refresh(self, db: Session) -> InventoryRefreshResult:
        records = await self.fetch()
        result = InventoryRefreshResult(received=len(records))

        for raw in records:
            normalized = self._normalize(raw)
            if not normalized["iccid"]:
                continue

            existing = db.scalar(
                select(MobileSIM).where(MobileSIM.iccid == normalized["iccid"])
            )
            if existing is None:
                db.add(MobileSIM(**normalized))
                result.imported += 1
                continue

            changed = False
            for field, value in normalized.items():
                if getattr(existing, field) != value:
                    setattr(existing, field, value)
                    changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1

        refreshed_at = datetime.now(timezone.utc)
        state = db.scalar(
            select(MobileSyncState).where(MobileSyncState.provider == "brandvno")
        )
        if state is None:
            state = MobileSyncState(provider="brandvno")
            db.add(state)
        state.last_success_at = refreshed_at
        state.last_attempt_at = refreshed_at
        state.last_error = ""
        state.records_received = result.received
        db.commit()
        result.refreshed_at = refreshed_at
        return result

    def record_failure(self, db: Session, error: str) -> None:
        state = db.scalar(
            select(MobileSyncState).where(MobileSyncState.provider == "brandvno")
        )
        if state is None:
            state = MobileSyncState(provider="brandvno")
            db.add(state)
        state.last_attempt_at = datetime.now(timezone.utc)
        state.last_error = error[:2000]
        db.commit()

    def _request_params(self) -> dict[str, Any] | None:
        params: dict[str, Any] = {}
        if self.settings.oxio_sim_page_size > 0:
            params[self.settings.oxio_sim_page_size_parameter] = (
                self.settings.oxio_sim_page_size
            )
        return params or None

    @classmethod
    def _extract_records(cls, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []

        preferred = ("sims", "items", "results", "resources", "records")
        for key in preferred:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            nested = cls._extract_records(data)
            if nested:
                return nested

        # Some APIs return a dictionary keyed by ICCID.
        values = list(payload.values())
        if values and all(isinstance(item, dict) for item in values):
            candidates = [item for item in values if isinstance(item, dict)]
            if any(cls._first(item, "iccid", "ICCID", "simIccid") for item in candidates):
                return candidates
        return []

    @classmethod
    def _normalize(cls, raw: dict[str, Any]) -> dict[str, Any]:
        iccid = cls._text(cls._first(raw, "iccid", "ICCID", "simIccid", "sim_iccid"))
        eid = cls._text(cls._first(raw, "eid", "EID", "simEid", "sim_eid"))
        provider_id = cls._text(
            cls._first(raw, "id", "simId", "sim_id", "resourceId", "uuid")
        ) or None
        raw_type = cls._text(
            cls._first(raw, "simType", "sim_type", "type", "formFactor", "format")
        ).lower()
        sim_type = "esim" if "esim" in raw_type or bool(eid) else "physical"

        raw_status = cls._text(
            cls._first(raw, "status", "state", "simStatus", "inventoryStatus")
        ).lower()
        status = cls._map_status(raw_status)
        activation_code = cls._text(
            cls._first(
                raw,
                "activationCode",
                "activation_code",
                "matchingId",
                "matching_id",
            )
        )

        return {
            "iccid": iccid,
            "sim_type": sim_type,
            "status": status,
            "eid": eid,
            "provider": "BrandVNO / OXIO",
            "provider_sim_id": provider_id,
            "activation_code": activation_code,
        }

    @staticmethod
    def _map_status(value: str) -> str:
        normalized = value.replace("-", "_").replace(" ", "_")
        mapping = {
            "": "available",
            "new": "available",
            "inventory": "available",
            "in_stock": "available",
            "ready": "available",
            "available": "available",
            "assigned": "assigned",
            "reserved": "assigned",
            "active": "active",
            "activated": "active",
            "suspended": "suspended",
            "inactive": "inactive",
            "deactivated": "inactive",
            "retired": "retired",
            "deleted": "retired",
        }
        return mapping.get(normalized, normalized[:30] or "available")

    @staticmethod
    def _first(data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data and data[key] is not None:
                return data[key]
        return None

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()
