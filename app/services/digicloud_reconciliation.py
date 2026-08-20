from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.database.customer_models import CustomerService
from app.providers.netsapiens import NetSapiensError, NetSapiensUsers


logger = logging.getLogger(__name__)

RECONCILABLE_STATUSES = {
    "active",
    "missing_from_digicloud",
    "external_delete_ignored",
    "billing_cleanup_required",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot(service: CustomerService) -> dict[str, Any]:
    try:
        value = json.loads(service.source_snapshot_json or "{}")
    except (TypeError, ValueError):
        value = {}
    return value if isinstance(value, dict) else {}


def _identity(value: Any) -> str:
    return str(value or "").strip().lower()


def _service_domain(service: CustomerService, snapshot: dict[str, Any]) -> str:
    domain = _identity(snapshot.get("domain"))
    if domain:
        return domain
    identifier = str(service.service_identifier or "")
    return _identity(identifier.rsplit("@", 1)[1]) if "@" in identifier else ""


def _service_username(service: CustomerService, snapshot: dict[str, Any]) -> str:
    username = _identity(snapshot.get("extension") or snapshot.get("username"))
    if username:
        return username
    return _identity(str(service.service_identifier or "").split("@", 1)[0])


def _live_identities(live_users: list[dict[str, Any]]) -> set[str]:
    identities: set[str] = set()
    for user in live_users:
        if not isinstance(user, dict):
            continue
        for key in ("username", "extension"):
            value = _identity(user.get(key))
            if value:
                identities.add(value)
    return identities


def reconcile_domain(
    db,
    domain: str,
    live_users: list[dict[str, Any]],
    *,
    confirmations: int = 2,
    checked_at: datetime | None = None,
    customer_id: int | None = None,
) -> dict[str, int]:
    """Reconcile NOP-managed subscribers after one successful domain read.

    API failures must be handled by the caller and must never invoke this
    function. A subscriber is marked missing only after consecutive successful
    inventory reads confirm its absence.
    """
    domain_key = _identity(domain).rstrip(".")
    now = checked_at or _utcnow()
    threshold = max(2, int(confirmations))
    live = _live_identities(live_users)
    result = {"checked": 0, "pending": 0, "missing": 0, "restored": 0, "unchanged": 0}

    statement = select(CustomerService).where(
        CustomerService.source_system == "digicloud",
        CustomerService.status.in_(RECONCILABLE_STATUSES),
    )
    if customer_id is not None:
        statement = statement.where(CustomerService.customer_id == customer_id)
    services = list(db.scalars(statement).all())
    for service in services:
        snapshot = _snapshot(service)
        if _service_domain(service, snapshot).rstrip(".") != domain_key:
            continue
        username = _service_username(service, snapshot)
        if not username:
            continue
        result["checked"] += 1
        snapshot["last_digicloud_check_at"] = now.isoformat()
        service.last_synced_at = now

        if username in live:
            was_missing = service.status in {
                "missing_from_digicloud", "external_delete_ignored", "billing_cleanup_required"
            }
            snapshot["consecutive_missing_checks"] = 0
            snapshot.pop("first_missing_at", None)
            snapshot.pop("confirmed_missing_at", None)
            snapshot["digicloud_presence"] = "active"
            if was_missing:
                service.status = "active"
                service.notes = "DigiCloud subscriber presence restored by reconciliation."
                result["restored"] += 1
            else:
                result["unchanged"] += 1
        else:
            misses = int(snapshot.get("consecutive_missing_checks") or 0) + 1
            snapshot["consecutive_missing_checks"] = misses
            snapshot.setdefault("first_missing_at", now.isoformat())
            if service.status == "external_delete_ignored":
                snapshot["digicloud_presence"] = "missing_ignored"
                result["unchanged"] += 1
            elif misses >= threshold:
                snapshot["digicloud_presence"] = "missing"
                snapshot["confirmed_missing_at"] = now.isoformat()
                service.status = "missing_from_digicloud"
                service.notes = (
                    f"Subscriber {username}@{domain_key} was absent from {misses} "
                    "consecutive successful DigiCloud inventory checks. Billing review required."
                )
                result["missing"] += 1
            else:
                snapshot["digicloud_presence"] = "verification_pending"
                result["pending"] += 1
        service.source_snapshot_json = json.dumps(snapshot, default=str, sort_keys=True)
    return result


def reconcile_all_domains(*, users_api: NetSapiensUsers | None = None) -> dict[str, Any]:
    """Run one complete reconciliation pass for every locally linked domain."""
    settings = get_settings()
    api = users_api or NetSapiensUsers()
    totals: dict[str, Any] = {
        "domains": 0, "checked": 0, "pending": 0, "missing": 0,
        "restored": 0, "unchanged": 0, "errors": [],
    }
    with SessionLocal() as db:
        services = list(db.scalars(select(CustomerService).where(
            CustomerService.source_system == "digicloud",
            CustomerService.status.in_(RECONCILABLE_STATUSES),
        )).all())
        domains = sorted({
            _service_domain(service, _snapshot(service)).rstrip(".")
            for service in services
            if _service_domain(service, _snapshot(service))
        })
        for domain in domains:
            try:
                live_users = api.list(domain)
            except NetSapiensError as exc:
                logger.warning("DigiCloud reconciliation skipped %s: %s", domain, exc)
                totals["errors"].append({"domain": domain, "error": str(exc)})
                continue
            summary = reconcile_domain(
                db,
                domain,
                live_users,
                confirmations=settings.digicloud_user_reconcile_confirmations,
            )
            totals["domains"] += 1
            for key, value in summary.items():
                totals[key] += value
            db.commit()
    return totals


_watcher_task: asyncio.Task | None = None


async def watcher_loop(interval_seconds: int) -> None:
    await asyncio.sleep(min(30, max(5, interval_seconds)))
    while True:
        try:
            await asyncio.to_thread(reconcile_all_domains)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("DigiCloud user reconciliation iteration failed")
        await asyncio.sleep(max(60, interval_seconds))


def start_watcher(interval_seconds: int = 900) -> asyncio.Task:
    global _watcher_task
    if _watcher_task and not _watcher_task.done():
        return _watcher_task
    _watcher_task = asyncio.create_task(watcher_loop(interval_seconds))
    return _watcher_task


async def stop_watcher() -> None:
    global _watcher_task
    if not _watcher_task:
        return
    _watcher_task.cancel()
    try:
        await _watcher_task
    except asyncio.CancelledError:
        pass
    _watcher_task = None
