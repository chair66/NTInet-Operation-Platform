from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.database.customer_models import ExternalRecordLink
from app.database.models import User
from app.security.context import SecurityContext
from app.services.platypus import PlatypusAPIError, PlatypusClient, PlatypusError
from app.services.platypus_customer_sync import PlatypusCustomerSync, _active_status
from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_BOOTSTRAP_STATUSES = frozenset({"active", "on_hold"})
DEFAULT_INACTIVE_MAX_AGE_MONTHS = 36
DISCOVERY_FALLBACK_TERMS = tuple(str(i) for i in range(10))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _external_id(row: dict) -> str:
    return str(row.get("id") or row.get("custid") or row.get("customer_id") or "").strip()


def _normalize_statuses(statuses: Iterable[str] | None) -> frozenset[str]:
    selected = frozenset(str(v).strip().lower() for v in (statuses or DEFAULT_BOOTSTRAP_STATUSES) if str(v).strip())
    return selected or DEFAULT_BOOTSTRAP_STATUSES




def _parse_platypus_date(value) -> datetime | None:
    raw = str(value or "").strip()
    if not raw or raw.upper() in {"NULL", "NONE", "N/A"}:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _months_ago(months: int, *, now: datetime | None = None) -> datetime:
    current = (now or _utcnow()).astimezone(timezone.utc)
    months = max(1, int(months))
    total = current.year * 12 + (current.month - 1) - months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    # Keep the day when possible; clamp to the last valid day in target month.
    import calendar
    day = min(current.day, calendar.monthrange(year, month)[1])
    return current.replace(year=year, month=month, day=day)


def _inactive_date(customer: dict) -> datetime | None:
    # deactivatedate is the primary lifecycle field. closeoutdate is a useful
    # fallback for older Platypus records where deactivatedate was never set.
    for key in ("deactivatedate", "closeoutdate"):
        parsed = _parse_platypus_date(customer.get(key))
        if parsed is not None:
            return parsed
    return None


async def _classify_inactive_rows(
    rows: list[dict],
    *,
    months: int = DEFAULT_INACTIVE_MAX_AGE_MONTHS,
    client: PlatypusClient | None = None,
    concurrency: int = 10,
) -> dict:
    """Classify inactive SearchCustomer rows by the detailed deactivation date."""
    client = client or PlatypusClient()
    cutoff = _months_ago(months)
    semaphore = asyncio.Semaphore(max(1, concurrency))
    recent_ids: set[str] = set()
    old_ids: set[str] = set()
    unknown_ids: set[str] = set()
    dates: dict[str, str] = {}

    async def classify(row: dict) -> None:
        external_id = _external_id(row)
        if not external_id:
            return
        try:
            async with semaphore:
                customer = await client.get_customer(external_id)
            inactive_at = _inactive_date(customer)
            if inactive_at is None:
                unknown_ids.add(external_id)
                return
            dates[external_id] = inactive_at.isoformat()
            if inactive_at < cutoff:
                old_ids.add(external_id)
            else:
                recent_ids.add(external_id)
        except Exception:
            # A failure to read the lifecycle date must never cause a customer to
            # be silently purged from eligibility. Treat it as unknown/reviewable.
            logger.exception("Unable to classify inactive Platypus customer %s by age", external_id)
            unknown_ids.add(external_id)

    await asyncio.gather(*(classify(row) for row in rows))
    return {
        "months": int(months),
        "cutoff": cutoff,
        "recent_ids": recent_ids,
        "old_ids": old_ids,
        "unknown_ids": unknown_ids,
        "dates": dates,
    }

def _summary_hash(row: dict) -> str:
    stable = {key: row.get(key) for key in sorted(row) if key.lower() not in {"modified"}}
    payload = json.dumps(stable, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class SyncProgress:
    running: bool = False
    mode: str = "idle"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    discovered: int = 0
    eligible: int = 0
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    excluded_old_inactive: int = 0
    inactive_date_unknown: int = 0
    last_customer_id: str = ""
    last_error: str = ""
    statuses: tuple[str, ...] = field(default_factory=lambda: tuple(sorted(DEFAULT_BOOTSTRAP_STATUSES)))

    def as_dict(self) -> dict:
        return {
            "running": self.running,
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "discovered": self.discovered,
            "eligible": self.eligible,
            "processed": self.processed,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "excluded_old_inactive": self.excluded_old_inactive,
            "inactive_date_unknown": self.inactive_date_unknown,
            "last_customer_id": self.last_customer_id,
            "last_error": self.last_error,
            "statuses": self.statuses,
        }


_progress = SyncProgress()
_bootstrap_task: asyncio.Task | None = None
_watcher_task: asyncio.Task | None = None


def progress_snapshot() -> dict:
    return _progress.as_dict()


async def discover_platypus_customers(
    client: PlatypusClient | None = None,
    *,
    diagnostics: dict | None = None,
) -> list[dict]:
    """Discover the complete Platypus customer population with SearchCustomer.

    Platypus documents SearchCustomer but no dedicated ListCustomers method.
    SearchCustomer's Search property is compared against name, attention, phone,
    customer id and username, and its WhereClause parameter can further restrict
    the result set.  For complete discovery we first issue an empty Search, which
    legacy Platypus treats as an unfiltered customer search.  Numeric probes are
    then used only to verify that the unfiltered result did not omit customers.

    If a probe finds a customer missing from the empty-search result, the code
    falls back to ID-range discovery using the documented WhereClause parameter.
    That fallback adaptively splits ranges when the server appears to be applying
    a result cap, so a UI/search result limit cannot silently truncate bootstrap.
    """
    client = client or PlatypusClient()
    diag = diagnostics if diagnostics is not None else {}
    diag.clear()
    diag.update({
        "strategy": "empty_search",
        "empty_search_count": 0,
        "probe_queries": 0,
        "probe_unique_count": 0,
        "probe_missing_from_empty": 0,
        "range_queries": 0,
        "highest_customer_id": 0,
        "result_cap_hint": 0,
        "verified_complete": False,
    })

    def add_rows(target: dict[str, dict], rows: list[dict]) -> None:
        for row in rows:
            external_id = _external_id(row)
            if external_id:
                target[external_id] = row

    # Primary path: the documented SearchCustomer method with an empty Search
    # property. This avoids the incorrect assumption that '%' is a SQL wildcard
    # in the Search property.
    try:
        empty_rows = await client.search_customers("")
    except PlatypusAPIError as exc:
        if exc.code == "DATA_ERROR":
            empty_rows = []
        else:
            raise
    merged: dict[str, dict] = {}
    add_rows(merged, empty_rows)
    diag["empty_search_count"] = len(empty_rows)

    # Cross-check with the old numeric probes. If every probed customer is already
    # present, the unfiltered SearchCustomer result is internally consistent and
    # can be used directly.
    probe_rows: dict[str, dict] = {}
    probe_sizes: list[int] = []
    for term in DISCOVERY_FALLBACK_TERMS:
        try:
            rows = await client.search_customers(term)
        except PlatypusAPIError as exc:
            if exc.code == "DATA_ERROR":
                rows = []
            else:
                raise
        diag["probe_queries"] += 1
        probe_sizes.append(len(rows))
        add_rows(probe_rows, rows)
    diag["probe_unique_count"] = len(probe_rows)
    missing_probe_ids = set(probe_rows) - set(merged)
    diag["probe_missing_from_empty"] = len(missing_probe_ids)

    if empty_rows and not missing_probe_ids:
        diag["strategy"] = "empty_search_verified"
        diag["verified_complete"] = True
        numeric_ids = [int(v) for v in merged if v.isdigit()]
        diag["highest_customer_id"] = max(numeric_ids, default=0)
        return _sort_customer_rows(merged.values())

    # Empty search appears truncated/unsupported. Preserve everything already
    # discovered and determine a conservative response-cap hint from the probes.
    add_rows(merged, list(probe_rows.values()))
    positive_sizes = [value for value in ([len(empty_rows)] + probe_sizes) if value > 0]
    cap_hint = min(positive_sizes) if positive_sizes else 50
    diag["result_cap_hint"] = cap_hint
    diag["strategy"] = "where_clause_id_ranges"

    numeric_ids = [int(v) for v in merged if v.isdigit()]
    highest_seen = max(numeric_ids, default=0)

    async def range_query(low: int, high: int) -> list[dict]:
        diag["range_queries"] += 1
        clause = f"customer.id >= {low} and customer.id <= {high}"
        try:
            return await client.search_customers("", where_clause=clause)
        except PlatypusAPIError as exc:
            if exc.code == "DATA_ERROR":
                return []
            raise

    # Find an upper boundary. We only need an existence test above the current
    # highest id; each successful query advances highest_seen.
    if highest_seen == 0:
        highest_seen = 1000
    for _ in range(32):
        clause = f"customer.id > {highest_seen}"
        diag["range_queries"] += 1
        try:
            rows = await client.search_customers("", where_clause=clause)
        except PlatypusAPIError as exc:
            if exc.code == "DATA_ERROR":
                rows = []
            else:
                raise
        ids = [int(_external_id(row)) for row in rows if _external_id(row).isdigit()]
        if not ids:
            break
        add_rows(merged, rows)
        next_high = max(ids)
        if next_high <= highest_seen:
            break
        highest_seen = next_high

    # Re-query 1..highest_seen in bounded windows. If a response reaches the
    # observed result-cap hint, recursively split the range until it is too small
    # to hide additional unique integer customer ids.
    async def collect_range(low: int, high: int) -> None:
        if low > high:
            return
        rows = await range_query(low, high)
        if not rows:
            return
        width = high - low + 1
        if len(rows) >= cap_hint and width > cap_hint:
            mid = (low + high) // 2
            await collect_range(low, mid)
            await collect_range(mid + 1, high)
            return
        add_rows(merged, rows)

    window = max(250, cap_hint * 20)
    low = 1
    while low <= highest_seen:
        high = min(highest_seen, low + window - 1)
        await collect_range(low, high)
        low = high + 1

    numeric_ids = [int(v) for v in merged if v.isdigit()]
    diag["highest_customer_id"] = max(numeric_ids, default=0)
    diag["verified_complete"] = True
    return _sort_customer_rows(merged.values())


def _sort_customer_rows(rows: Iterable[dict]) -> list[dict]:
    def sort_key(row: dict):
        value = _external_id(row)
        return (0, int(value)) if value.isdigit() else (1, value)
    return sorted(rows, key=sort_key)


async def bootstrap_preview(
    statuses: Iterable[str] | None = None,
    *,
    exclude_old_inactive: bool = True,
    inactive_max_age_months: int = DEFAULT_INACTIVE_MAX_AGE_MONTHS,
) -> dict:
    selected = _normalize_statuses(statuses)
    diagnostics: dict = {}
    rows = await discover_platypus_customers(diagnostics=diagnostics)
    status_counts = {key: 0 for key in ("active", "on_hold", "suspended", "inactive")}
    for row in rows:
        status_counts[_active_status(row.get("active"))] += 1

    eligible = [row for row in rows if _active_status(row.get("active")) in selected]
    inactive_age = {
        "months": int(inactive_max_age_months),
        "cutoff": _months_ago(inactive_max_age_months),
        "recent_ids": set(), "old_ids": set(), "unknown_ids": set(), "dates": {},
    }
    if "inactive" in selected:
        inactive_rows = [row for row in rows if _active_status(row.get("active")) == "inactive"]
        inactive_age = await _classify_inactive_rows(inactive_rows, months=inactive_max_age_months)
        if exclude_old_inactive:
            old_ids = inactive_age["old_ids"]
            eligible = [row for row in eligible if _external_id(row) not in old_ids]

    ids = {_external_id(row) for row in eligible if _external_id(row)}
    with SessionLocal() as db:
        linked = set(db.scalars(select(ExternalRecordLink.external_id).where(
            ExternalRecordLink.system_name == "platypus",
            ExternalRecordLink.record_type == "customer",
            ExternalRecordLink.external_id.in_(ids) if ids else False,
        ))) if ids else set()
    return {
        "discovered": len(rows),
        "eligible": len(eligible),
        "already_linked": len(ids & linked),
        "new_to_nop": len(ids - linked),
        "status_counts": status_counts,
        "statuses": tuple(sorted(selected)),
        "sample": eligible[:100],
        "diagnostics": diagnostics,
        "inactive_policy": {
            "enabled": bool(exclude_old_inactive),
            "months": int(inactive_max_age_months),
            "cutoff": inactive_age["cutoff"],
            "recent": len(inactive_age["recent_ids"]),
            "old": len(inactive_age["old_ids"]),
            "unknown": len(inactive_age["unknown_ids"]),
        },
    }


def _system_context() -> SecurityContext:
    with SessionLocal() as db:
        user = db.scalar(
            select(User)
            .options(
                selectinload(User.roles),
                selectinload(User.organization),
            )
            .where(User.is_superuser.is_(True), User.active.is_(True))
            .order_by(User.id.asc())
        )
        if user is None:
            user = db.scalar(select(User).where(User.active.is_(True)).order_by(User.id.asc()))
        if user is None:
            raise RuntimeError("NOP has no active user available for Platypus background synchronization.")
        # Build while the relationships/session are alive.
        return SecurityContext.from_user(user)


async def _sync_one(external_id: str, context: SecurityContext) -> tuple[bool, int]:
    client = PlatypusClient()
    profile = await client.get_ticketing_customer(external_id)
    with SessionLocal() as db:
        existing = db.scalar(select(ExternalRecordLink).where(
            ExternalRecordLink.system_name == "platypus",
            ExternalRecordLink.record_type == "customer",
            ExternalRecordLink.external_id == external_id,
        ))
        customer = PlatypusCustomerSync(db, context).sync(profile)
        db.commit()
        return existing is None, customer.id


async def run_bootstrap(statuses: Iterable[str] | None = None, *, only_new: bool = False, mode: str = "bootstrap", exclude_old_inactive: bool = True, inactive_max_age_months: int = DEFAULT_INACTIVE_MAX_AGE_MONTHS) -> None:
    global _progress
    selected = _normalize_statuses(statuses)
    _progress = SyncProgress(
        running=True,
        mode=mode,
        started_at=_utcnow(),
        statuses=tuple(sorted(selected)),
    )
    try:
        rows = await discover_platypus_customers()
        _progress.discovered = len(rows)
        eligible = [row for row in rows if _active_status(row.get("active")) in selected]
        if "inactive" in selected and exclude_old_inactive:
            inactive_rows = [row for row in rows if _active_status(row.get("active")) == "inactive"]
            inactive_age = await _classify_inactive_rows(inactive_rows, months=inactive_max_age_months)
            _progress.excluded_old_inactive = len(inactive_age["old_ids"])
            _progress.inactive_date_unknown = len(inactive_age["unknown_ids"])
            eligible = [row for row in eligible if _external_id(row) not in inactive_age["old_ids"]]
        _progress.eligible = len(eligible)
        context = _system_context()

        for row in eligible:
            external_id = _external_id(row)
            if not external_id:
                _progress.skipped += 1
                continue
            _progress.last_customer_id = external_id
            try:
                row_hash = _summary_hash(row)
                if only_new:
                    settings = get_settings()
                    with SessionLocal() as db:
                        link = db.scalar(select(ExternalRecordLink).where(
                            ExternalRecordLink.system_name == "platypus",
                            ExternalRecordLink.record_type == "customer",
                            ExternalRecordLink.external_id == external_id,
                        ))
                        if link is not None:
                            stale_before = _utcnow() - timedelta(hours=max(1, settings.platypus_customer_full_refresh_hours))
                            summary_changed = bool(link.sync_hash and link.sync_hash != row_hash)
                            full_refresh_due = link.last_synced_at is None or link.last_synced_at < stale_before
                            if not summary_changed and not full_refresh_due:
                                link.last_seen_at = _utcnow()
                                db.commit()
                                _progress.skipped += 1
                                continue
                created, _ = await _sync_one(external_id, context)
                with SessionLocal() as db:
                    link = db.scalar(select(ExternalRecordLink).where(
                        ExternalRecordLink.system_name == "platypus",
                        ExternalRecordLink.record_type == "customer",
                        ExternalRecordLink.external_id == external_id,
                    ))
                    if link is not None:
                        link.sync_hash = row_hash
                        link.last_seen_at = _utcnow()
                        db.commit()
                if created:
                    _progress.created += 1
                else:
                    _progress.updated += 1
            except Exception as exc:  # continue the batch and expose the last failure
                logger.exception("Platypus customer sync failed for %s", external_id)
                _progress.failed += 1
                _progress.last_error = f"Customer {external_id}: {exc}"
            finally:
                _progress.processed += 1
    except Exception as exc:
        logger.exception("Platypus bootstrap failed")
        _progress.last_error = str(exc)
    finally:
        _progress.running = False
        _progress.finished_at = _utcnow()


def start_bootstrap(statuses: Iterable[str] | None = None, *, exclude_old_inactive: bool = True, inactive_max_age_months: int = DEFAULT_INACTIVE_MAX_AGE_MONTHS) -> bool:
    global _bootstrap_task
    if _progress.running or (_bootstrap_task and not _bootstrap_task.done()):
        return False
    _bootstrap_task = asyncio.create_task(run_bootstrap(statuses, only_new=False, mode="bootstrap", exclude_old_inactive=exclude_old_inactive, inactive_max_age_months=inactive_max_age_months))
    return True


async def watcher_loop(interval_seconds: int, statuses: Iterable[str] | None = None) -> None:
    # Delay first run so application startup is not blocked by an external service.
    await asyncio.sleep(min(30, max(5, interval_seconds)))
    while True:
        try:
            if not _progress.running:
                await run_bootstrap(statuses, only_new=True, mode="watcher", exclude_old_inactive=True, inactive_max_age_months=DEFAULT_INACTIVE_MAX_AGE_MONTHS)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Platypus customer watcher iteration failed")
        await asyncio.sleep(max(60, interval_seconds))


def start_watcher(interval_seconds: int = 300, statuses: Iterable[str] | None = None) -> asyncio.Task:
    global _watcher_task
    if _watcher_task and not _watcher_task.done():
        return _watcher_task
    _watcher_task = asyncio.create_task(watcher_loop(interval_seconds, statuses))
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
