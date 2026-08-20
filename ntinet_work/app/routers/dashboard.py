from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.dependencies import bw
from app.services.bandwidth import BandwidthAPIError
from app.web import render
from app.security import filter_bandwidth_records, visible_bandwidth_sites
from app.routers.porting import _port_items
from app.database.core import get_db
from app.database.models import PortDraft
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter()


def _get_ci(data: dict[str, Any], *keys: str) -> Any:
    wanted = {key.casefold() for key in keys}
    for key, value in data.items():
        if str(key).casefold() in wanted:
            return value
    return None


def _order_items(data: Any) -> list[dict[str, Any]]:
    """Extract number-order summaries from JSON or XML-shaped responses."""
    found: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return
        order_id = _get_ci(value, "orderId", "OrderId", "id")
        status = _get_ci(value, "orderStatus", "OrderStatus", "status", "Status")
        if order_id and status:
            completed = _get_ci(value, "completedNumbers", "CompletedNumbers", "completedQuantity")
            total = _get_ci(value, "totalQuantity", "TotalQuantity", "quantity", "Quantity")
            found.append({
                **value,
                "orderId": str(order_id),
                "status": str(status),
                "completedNumbers": completed or total or 0,
                "createdDate": _get_ci(value, "createdDate", "CreatedDate", "orderCreateDate", "OrderCreateDate") or "",
            })
            return
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(nested)

    walk(data)
    return list({item["orderId"]: item for item in found}.values())


def _number_count(port: dict[str, Any]) -> int:
    value = port.get("countOfPhoneNumbers")
    try:
        return int(value)
    except (TypeError, ValueError):
        numbers = port.get("phoneNumbers") or []
        return len(numbers) if isinstance(numbers, list) else 1


def _is_completed(status: str) -> bool:
    text = (status or "").strip().casefold().replace("-", "_")
    return text in {"complete", "completed", "cancelled", "canceled", "failed", "partial"} or text.startswith("complete")


def _is_exception(status: str) -> bool:
    text = (status or "").casefold()
    # Completed/closed orders must not remain in the active exception count.
    return not _is_completed(status) and any(
        word in text for word in ("exception", "error", "attention", "rejected", "failed")
    )


def _is_foc(port: dict[str, Any]) -> bool:
    status = str(port.get("processingStatus") or "")
    if _is_completed(status) or _is_exception(status):
        return False
    text = status.casefold().replace("-", "_").replace(" ", "_")
    has_foc_date = bool(
        port.get("actualFocDate")
        or port.get("requestedFocDate")
        or port.get("focDate")
    )
    return has_foc_date or "foc" in text or "firm_order_commitment" in text


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, q: str = "", db: Session = Depends(get_db)):
    error = None
    sites: list[dict[str, Any]] = []
    total_numbers = 0
    portins: list[dict[str, Any]] = []
    number_orders: list[dict[str, Any]] = []
    search_results: list[dict[str, str]] = []

    try:
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        totals_task = asyncio.gather(
            *(bw.inventory.site_total(site.get("id")) for site in sites),
            return_exceptions=True,
        )
        ports_task = bw.porting.list(page=1, size=300)
        orders_task = bw.ordering.list(page=1, size=100)
        totals, raw_ports, raw_orders = await asyncio.gather(
            totals_task, ports_task, orders_task, return_exceptions=True
        )

        if isinstance(totals, list):
            for site, count in zip(sites, totals):
                site["portal_number_count"] = count if isinstance(count, int) else 0
                total_numbers += site["portal_number_count"]

        if not isinstance(raw_ports, Exception):
            portins = filter_bandwidth_records(
                request, _port_items(raw_ports), "subAccountId", "siteId"
            )
        if not isinstance(raw_orders, Exception):
            number_orders = _order_items(raw_orders)

        query = q.strip()
        if query:
            query_digits = "".join(ch for ch in query if ch.isdigit())
            query_folded = query.casefold()
            for port in portins:
                candidates = (
                    str(port.get("orderId", "")),
                    str(port.get("customerOrderId", "")),
                    str(port.get("billingPhoneNumber", "")),
                )
                if any(query_folded in value.casefold() for value in candidates if value):
                    search_results.append({
                        "type": "Port order",
                        "primary": str(port.get("orderId", "")),
                        "secondary": str(port.get("processingStatus", "")),
                        "url": f"/ports/{port.get('orderId')}",
                    })

            for order in number_orders:
                order_id = str(order.get("orderId", ""))
                if query_folded in order_id.casefold():
                    search_results.append({
                        "type": "Number order",
                        "primary": order_id,
                        "secondary": str(order.get("status", "")),
                        "url": "/orders",
                    })

            # Number inventory lookup only runs for a telephone-number-shaped query.
            if len(query_digits) >= 7:
                normalized = query_digits[-10:]
                for site in sites:
                    try:
                        locations = await bw.inventory.list_locations(site.get("id"))
                    except BandwidthAPIError:
                        continue
                    for location in locations:
                        try:
                            numbers = await bw.inventory.list_numbers(site.get("id"), location.get("id"), size=5000)
                        except BandwidthAPIError:
                            continue
                        for number in numbers:
                            tn = str(number.get("phoneNumber", ""))
                            digits = "".join(ch for ch in tn if ch.isdigit())
                            if digits.endswith(normalized):
                                search_results.append({
                                    "type": "Telephone number",
                                    "primary": tn,
                                    "secondary": f"{site.get('name', '')} · {location.get('name', '')}",
                                    "url": f"/sites/{site.get('id')}/locations/{location.get('id')}/numbers/{tn}?site_name={site.get('name','')}&location_name={location.get('name','')}",
                                })
    except BandwidthAPIError as exc:
        error = exc.diagnostic


    # Merge locally submitted orders immediately. The provider list may lag for
    # a short period after a successful submission.
    user = request.state.user
    local_submitted = list(db.scalars(select(PortDraft).where(
        PortDraft.organization_id == user.organization_id,
        PortDraft.bandwidth_order_id.is_not(None),
        PortDraft.status == "submitted",
    )))
    known_ids = {str(item.get("orderId") or "") for item in portins}
    for draft in local_submitted:
        if str(draft.bandwidth_order_id) not in known_ids:
            portins.append({
                "orderId": draft.bandwidth_order_id,
                "customerOrderId": draft.nti_reference,
                "billingPhoneNumber": draft.billing_telephone_number,
                "processingStatus": draft.bandwidth_status or "SUBMITTED",
                "losingCarrierName": draft.losing_carrier_name,
                "lastModifiedDate": draft.updated_at.isoformat() if draft.updated_at else "",
                "countOfPhoneNumbers": 0,
                "localPendingSync": True,
            })

    recent_ports = sorted(
        portins,
        key=lambda item: str(item.get("lastModifiedDate", "")),
        reverse=True,
    )[:8]
    exception_ports = [p for p in portins if _is_exception(str(p.get("processingStatus", "")))]
    foc_ports = [p for p in portins if _is_foc(p)]
    open_orders = [
        p for p in portins
        if not _is_completed(str(p.get("processingStatus", "")))
        and not _is_exception(str(p.get("processingStatus", "")))
        and not _is_foc(p)
    ]
    draft_count = db.scalar(
        select(func.count())
        .select_from(PortDraft)
        .where(
            PortDraft.organization_id == user.organization_id,
            PortDraft.status.notin_(["submitted", "completed", "cancelled", "canceled"]),
            PortDraft.bandwidth_order_id.is_(None),
        )
    ) or 0

    return render(
        request,
        "dashboard.html",
        sites=sites,
        total_numbers=total_numbers,
        open_order_count=len(open_orders),
        draft_order_count=draft_count,
        foc_order_count=len(foc_ports),
        exception_count=len(exception_ports),
        recent_ports=recent_ports,
        q=q,
        search_results=search_results,
        error=error,
    )
