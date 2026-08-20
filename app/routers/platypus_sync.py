from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.database import SessionLocal
from app.database.customer_models import ExternalRecordLink
from app.security import require_permission, require_platform_staff
from app.services.platypus import PlatypusError
from app.services.platypus_bootstrap import DEFAULT_INACTIVE_MAX_AGE_MONTHS, bootstrap_preview, progress_snapshot, start_bootstrap
from app.config import get_settings
from app.web import render

router = APIRouter(prefix="/admin/sync/platypus", tags=["Administration"])
VALID_STATUSES = {"active", "on_hold", "suspended", "inactive"}


def _require(request: Request) -> None:
    require_permission(request, "admin.organizations")
    require_platform_staff(request)



def _inactive_policy(request: Request) -> tuple[bool, int]:
    raw_enabled = request.query_params.get("exclude_old_inactive", "1")
    enabled = str(raw_enabled).strip().lower() not in {"0", "false", "no", "off"}
    try:
        months = int(request.query_params.get("inactive_months", str(DEFAULT_INACTIVE_MAX_AGE_MONTHS)))
    except (TypeError, ValueError):
        months = DEFAULT_INACTIVE_MAX_AGE_MONTHS
    return enabled, max(1, min(months, 240))


def _selected(request: Request) -> set[str]:
    raw = request.query_params.getlist("status")
    selected = {value for value in raw if value in VALID_STATUSES}
    return selected or {"active", "on_hold"}


@router.get("")
async def sync_home(request: Request):
    _require(request)
    statuses = _selected(request)
    preview = None
    error = None
    exclude_old_inactive, inactive_months = _inactive_policy(request)
    if request.query_params.get("discover") == "1":
        try:
            preview = await bootstrap_preview(statuses, exclude_old_inactive=exclude_old_inactive, inactive_max_age_months=inactive_months)
        except PlatypusError as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Unable to discover Platypus customers: {exc}"
    with SessionLocal() as db:
        links = db.scalar(select(func.count()).select_from(ExternalRecordLink).where(
            ExternalRecordLink.system_name == "platypus",
            ExternalRecordLink.record_type == "customer",
        )) or 0
        last_sync = db.scalar(select(func.max(ExternalRecordLink.last_synced_at)).where(
            ExternalRecordLink.system_name == "platypus",
            ExternalRecordLink.record_type == "customer",
        ))
    return render(
        request,
        "admin/platypus_sync.html",
        preview=preview,
        sync_error=error,
        selected_statuses=statuses,
        progress=progress_snapshot(),
        linked_count=links,
        last_sync=last_sync,
        sync_settings=get_settings(),
        exclude_old_inactive=exclude_old_inactive,
        inactive_months=inactive_months,
    )


@router.post("/start")
async def start_sync(request: Request, status: list[str] = Form(default=[]), exclude_old_inactive: str = Form(default="1"), inactive_months: int = Form(default=DEFAULT_INACTIVE_MAX_AGE_MONTHS)):
    _require(request)
    selected = {value for value in status if value in VALID_STATUSES} or {"active", "on_hold"}
    exclude_old = str(exclude_old_inactive).strip().lower() not in {"0", "false", "no", "off"}
    months = max(1, min(int(inactive_months), 240))
    started = start_bootstrap(selected, exclude_old_inactive=exclude_old, inactive_max_age_months=months)
    message = "started" if started else "running"
    query = "&".join(f"status={value}" for value in sorted(selected))
    query += f"&exclude_old_inactive={1 if exclude_old else 0}&inactive_months={months}"
    return RedirectResponse(f"/admin/sync/platypus?discover=1&sync={message}&{query}", status_code=303)
