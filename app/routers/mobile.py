from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.database import SessionLocal
from app.database.mobile_models import (
    MobileCustomer,
    MobileException,
    MobileLine,
    MobileOrder,
    MobilePlan,
    MobilePortRequest,
    MobileSIM,
    MobileSyncState,
)
from app.providers.mobile import BrandVNOMobileProvider, MobileProviderError
from app.security import require_permission, require_platform_staff
from app.web import render


router = APIRouter(prefix="/mobile", tags=["NTI Mobile"])


def mobile_staff(request: Request, permission: str) -> None:
    require_platform_staff(request)
    require_permission(request, permission)


def scalar_count(db, model, *criteria) -> int:
    statement = select(func.count()).select_from(model)
    if criteria:
        statement = statement.where(*criteria)
    return int(db.scalar(statement) or 0)


@router.get("")
@router.get("/")
def mobile_dashboard(request: Request):
    mobile_staff(request, "nti_mobile.dashboard")

    with SessionLocal() as db:
        metrics = {
            "active_lines": scalar_count(
                db,
                MobileLine,
                MobileLine.status == "active",
            ),
            "pending_activations": scalar_count(
                db,
                MobileLine,
                MobileLine.status.in_(("pending", "activating")),
            ),
            "port_requests": scalar_count(
                db,
                MobilePortRequest,
                MobilePortRequest.status.not_in(
                    ("completed", "cancelled", "rejected")
                ),
            ),
            "physical_sims": scalar_count(
                db,
                MobileSIM,
                MobileSIM.sim_type == "physical",
                MobileSIM.status == "available",
            ),
            "esims": scalar_count(
                db,
                MobileSIM,
                MobileSIM.sim_type == "esim",
                MobileSIM.status == "available",
            ),
            "exceptions": scalar_count(
                db,
                MobileException,
                MobileException.status == "open",
            ),
        }

        recent_orders = list(
            db.scalars(
                select(MobileOrder)
                .order_by(MobileOrder.created_at.desc())
                .limit(8)
            )
        )
        recent_exceptions = list(
            db.scalars(
                select(MobileException)
                .where(MobileException.status == "open")
                .order_by(MobileException.created_at.desc())
                .limit(6)
            )
        )

    return render(
        request,
        "mobile/dashboard.html",
        page_title="NTI Mobile",
        page_description=(
            "Mobile subscriber, SIM, activation, and porting operations."
        ),
        metrics=metrics,
        recent_orders=recent_orders,
        recent_exceptions=recent_exceptions,
        active_section="dashboard",
    )


@router.get("/orders")
def mobile_orders(request: Request):
    mobile_staff(request, "nti_mobile.orders.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobileOrder)
                .order_by(MobileOrder.created_at.desc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Orders",
        page_description=(
            "Activations, plan changes, SIM swaps, and service orders."
        ),
        active_section="orders",
        record_type="orders",
        records=records,
        empty_title="No mobile orders",
        empty_message="New mobile orders will appear here.",
        create_url="/mobile/orders/new",
        create_label="New Mobile Order",
        can_create=request.state.user.can("nti_mobile.orders.create"),
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/orders/new")
def mobile_order_new(request: Request):
    mobile_staff(request, "nti_mobile.orders.create")

    return render(
        request,
        "mobile/foundation.html",
        page_title="New Mobile Order",
        page_description=(
            "Order entry will be enabled in the next mobile workflow milestone."
        ),
        active_section="orders",
    )


@router.get("/customers")
def mobile_customers(request: Request):
    mobile_staff(request, "nti_mobile.customers.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobileCustomer)
                .order_by(MobileCustomer.created_at.desc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Customers",
        page_description="NTI Mobile end users and customer accounts.",
        active_section="customers",
        record_type="customers",
        records=records,
        empty_title="No mobile customers",
        empty_message="Customers created through mobile ordering will appear here.",
        create_url="",
        create_label="",
        can_create=False,
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/lines")
def mobile_lines(request: Request):
    mobile_staff(request, "nti_mobile.lines.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobileLine)
                .order_by(MobileLine.created_at.desc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Lines",
        page_description="Active, pending, suspended, and disconnected lines.",
        active_section="lines",
        record_type="lines",
        records=records,
        empty_title="No mobile lines",
        empty_message="Activated and pending mobile lines will appear here.",
        create_url="",
        create_label="",
        can_create=False,
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/sims")
async def mobile_sims(request: Request):
    mobile_staff(request, "nti_mobile.sims.read")

    provider = BrandVNOMobileProvider()
    sync_error = ""
    sync_summary = ""
    used_cached_inventory = False
    can_manage_sims = request.state.user.can("nti_mobile.sims.manage")

    with SessionLocal() as db:
        if can_manage_sims:
            try:
                result = await provider.sim_inventory.refresh(db)
                sync_summary = (
                    f"Inventory refreshed: {result.imported} new, "
                    f"{result.updated} updated, {result.unchanged} unchanged."
                )
            except MobileProviderError as exc:
                sync_error = str(exc)
                used_cached_inventory = True
                provider.sim_inventory.record_failure(db, sync_error)

        records = list(
            db.scalars(
                select(MobileSIM)
                .order_by(MobileSIM.updated_at.desc(), MobileSIM.iccid.asc())
            )
        )
        sync_state = db.scalar(
            select(MobileSyncState).where(
                MobileSyncState.provider == "brandvno"
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="SIM Management",
        page_description=(
            "Read-only physical SIM and eSIM inventory refreshed from OXIO."
        ),
        active_section="sims",
        record_type="sims",
        records=records,
        empty_title="No SIM inventory available",
        empty_message=(
            "Refresh Inventory will retrieve SIMs from OXIO once the BrandVNO "
            "inventory endpoint is configured."
        ),
        create_url="",
        create_label="",
        can_create=False,
        sync_url="/mobile/sims",
        sync_label="Refresh Inventory",
        can_sync=can_manage_sims,
        sync_error=sync_error,
        sync_summary=sync_summary,
        sync_state=sync_state,
        used_cached_inventory=used_cached_inventory,
    )


@router.get("/sims/sync")
@router.get("/sims/refresh")
def mobile_sim_refresh(request: Request):
    mobile_staff(request, "nti_mobile.sims.manage")
    return RedirectResponse("/mobile/sims", status_code=303)


@router.get("/numbers")
def mobile_numbers(request: Request):
    mobile_staff(request, "nti_mobile.numbers.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobileLine)
                .where(MobileLine.mobile_number != "")
                .order_by(MobileLine.mobile_number.asc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Numbers",
        page_description="Telephone numbers assigned to NTI Mobile lines.",
        active_section="numbers",
        record_type="numbers",
        records=records,
        empty_title="No assigned mobile numbers",
        empty_message="Numbers will appear after assignment or activation.",
        create_url="",
        create_label="",
        can_create=False,
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/plans")
def mobile_plans(request: Request):
    mobile_staff(request, "nti_mobile.plans.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobilePlan)
                .order_by(MobilePlan.data_gb.asc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Plans",
        page_description="Service plans, data allowances, and top-up pricing.",
        active_section="plans",
        record_type="plans",
        records=records,
        empty_title="No mobile plans",
        empty_message="Run the included plan seed command to add starter plans.",
        create_url="",
        create_label="",
        can_create=False,
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/ports")
def mobile_ports(request: Request):
    mobile_staff(request, "nti_mobile.ports.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobilePortRequest)
                .order_by(MobilePortRequest.created_at.desc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Port Requests",
        page_description="Number transfers into NTI Mobile.",
        active_section="ports",
        record_type="ports",
        records=records,
        empty_title="No mobile port requests",
        empty_message="New mobile port requests will appear here.",
        create_url="/mobile/ports/new",
        create_label="New Port Request",
        can_create=request.state.user.can("nti_mobile.ports.create"),
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/ports/new")
def mobile_port_new(request: Request):
    mobile_staff(request, "nti_mobile.ports.create")

    return render(
        request,
        "mobile/foundation.html",
        page_title="New Mobile Port Request",
        page_description=(
            "Mobile port entry will be enabled with the ordering workflow."
        ),
        active_section="ports",
    )


@router.get("/exceptions")
def mobile_exceptions(request: Request):
    mobile_staff(request, "nti_mobile.exceptions.read")

    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(MobileException)
                .order_by(MobileException.created_at.desc())
            )
        )

    return render(
        request,
        "mobile/list.html",
        page_title="Mobile Exceptions",
        page_description="Mobile workflows requiring investigation or action.",
        active_section="exceptions",
        record_type="exceptions",
        records=records,
        empty_title="No mobile exceptions",
        empty_message="There are currently no mobile workflow exceptions.",
        create_url="",
        create_label="",
        can_create=False,
        sync_url="",
        sync_label="",
        can_sync=False,
    )


@router.get("/settings")
def mobile_settings(request: Request):
    mobile_staff(request, "nti_mobile.settings")

    return render(
        request,
        "mobile/foundation.html",
        page_title="NTI Mobile Settings",
        page_description=(
            "Provider and workflow configuration will be added after the data foundation."
        ),
        active_section="settings",
    )
