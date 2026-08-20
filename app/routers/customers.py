from __future__ import annotations

from datetime import date, datetime, timezone
import json
from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from urllib.parse import quote_plus, urlencode

from app.services.customer_directory import CustomerDirectory
from app.config import get_settings
from app.services.platypus_customer_sync import PlatypusCustomerSync
from app.database import SessionLocal
from app.database.models import DigiCloudPhoneNumber
from app.database.customer_models import (
    Customer,
    CustomerContact,
    CustomerLocation,
    CustomerService,
    ExternalRecordLink,
    PlumeCustomerNetwork,
)
from app.database.ticket_models import Ticket
from app.database.job_models import Job
from app.database.catalog_models import Estimate
from app.security import context_from_request, require_permission, require_platform_staff
from app.services.audit_service import AuditService
from app.services.customer_merge_service import CustomerMergeService
from app.services.customer_service import CustomerService as LocalCustomerService
from app.services.plume_read_service import PlumeReadService
from app.services.plume_provisioning_service import PlumeProvisioningService
from app.providers.plume import PlumeError
from app.services.platypus import PlatypusClient, PlatypusError
from app.services.digicloud_service import DigiCloudService
from app.services.digicloud_reconciliation import reconcile_domain
from app.providers.netsapiens import NetSapiensDevices, NetSapiensError, NetSapiensUsers
from app.providers.netsapiens.answering_rules import NetSapiensAnsweringRules
from app.providers.netsapiens.phonenumbers import NetSapiensPhoneNumbers
from app.providers.netsapiens.emergency_addresses import NetSapiensEmergencyAddresses
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from app.web import render

router = APIRouter(prefix="/customers", tags=["customers"])
api_router = APIRouter(prefix="/api/customers", tags=["customers-api"])


def _directory() -> CustomerDirectory:
    return CustomerDirectory()


@router.get("/new")
async def new_customer_wizard(request: Request, local_customer_id: int | None = None):
    require_platform_staff(request)
    require_permission(request, "customers.manage")
    customer = None
    with SessionLocal() as db:
        if local_customer_id:
            customer = db.get(Customer, local_customer_id)
        return render(
            request,
            "customers/new_wizard.html",
            customer=customer,
            error=request.query_params.get("error", ""),
        )


@router.post("/new")
async def create_customer_wizard(
    request: Request,
    local_customer_id: int | None = Form(None),
    name: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(""),
    email: str = Form(...),
    phone: str = Form(...),
    address_line_1: str = Form(...),
    address_line_2: str = Form(""),
    city: str = Form(...),
    state: str = Form("SC"),
    postal_code: str = Form(...),
    country: str = Form("US"),
    store_id: str = Form("1"),
):
    require_platform_staff(request)
    require_permission(request, "customers.manage")
    context = context_from_request(request)
    with SessionLocal() as db:
        local = db.get(Customer, local_customer_id) if local_customer_id else None
        try:
            if local is None:
                local = LocalCustomerService(db, context).create_customer(
                    name=name,
                    customer_type="direct",
                    status="active",
                    owner_organization_id=context.organization_id,
                    servicing_organization_id=context.organization_id,
                    billing_method="direct",
                    billing_email=email,
                    billing_phone=phone,
                    notes="Platypus provisioning pending.",
                )
                contact = CustomerContact(
                    customer=local,
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    email=email.strip().lower(),
                    office_phone=phone.strip(),
                    is_primary=True,
                    receives_invoices=True,
                )
                location = CustomerLocation(
                    customer=local,
                    name="Primary Location",
                    address_line_1=address_line_1.strip(),
                    address_line_2=address_line_2.strip(),
                    city=city.strip(),
                    state=state.strip().upper(),
                    postal_code=postal_code.strip(),
                    country=country.strip().upper() or "US",
                    is_primary=True,
                )
                db.add_all([contact, location])
                db.commit()
                db.refresh(local)

            existing_link = db.scalar(select(ExternalRecordLink).where(
                ExternalRecordLink.customer_id == local.id,
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
            ))
            if existing_link:
                return RedirectResponse(
                    f"/customers/{existing_link.external_id}/rates/manage", 303
                )

            created = await PlatypusClient().add_customer(
                name=local.name,
                phone=phone,
                username=email,
                email=email,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                billing_method="check",
                store_id=store_id,
            )
            platypus_id = created["customer_id"]
            link = ExternalRecordLink(
                customer_id=local.id,
                system_name="platypus",
                record_type="customer",
                external_id=platypus_id,
                external_account_number=platypus_id,
                link_status="active",
                source_snapshot_json=json.dumps({
                    "name": local.name,
                    "email": email.strip().lower(),
                    "phone": phone.strip(),
                    "store_id": store_id.strip(),
                }, sort_keys=True),
                notes="Created by the NOP staff customer wizard.",
            )
            db.add(link)
            local.notes = "Platypus customer created. Continue the wizard to add rates and services."
            AuditService(db, request, context).record(
                "platypus.customer.create",
                "customer",
                local.id,
                f"Created Platypus customer {platypus_id} for {local.customer_number}",
                module="customer-management",
                organization_id=local.owner_organization_id,
                event_data={"platypus_customer_id": platypus_id},
            )
            db.commit()
            return render(
                request,
                "customers/new_wizard_complete.html",
                customer=local,
                platypus_customer_id=platypus_id,
                portal_username=created["username"],
                temporary_password=created["temporary_password"],
            )
        except (ValueError, PlatypusError, SQLAlchemyError) as exc:
            db.rollback()
            if local is not None:
                persisted = db.get(Customer, local.id)
                if persisted is not None:
                    persisted.notes = f"Platypus provisioning pending: {exc}"
                    db.commit()
            return render(
                request,
                "customers/new_wizard.html",
                status_code=400,
                customer=local,
                error=str(exc),
                values={
                    "name": name, "first_name": first_name, "last_name": last_name,
                    "email": email, "phone": phone, "address_line_1": address_line_1,
                    "address_line_2": address_line_2, "city": city, "state": state,
                    "postal_code": postal_code, "country": country, "store_id": store_id,
                },
            )


def _customer_phone_numbers(profile: dict) -> list[str]:
    """Return unique, populated customer phone numbers for profile display."""
    customer = profile.get("customer") or {}
    candidates: list[str] = []

    primary = customer.get("phonemasked") or customer.get("phone")
    if primary:
        candidates.append(str(primary).strip())

    for phone in profile.get("phones") or []:
        if not isinstance(phone, dict):
            continue
        value = phone.get("phonemasked") or phone.get("number") or phone.get("phone")
        if value:
            candidates.append(str(value).strip())

    result: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        normalized = "".join(ch for ch in value if ch.isdigit())
        key = normalized or value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _digits(value: object) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _destination_user(row: dict) -> str:
    """Extract the subscriber/extension a live DigiCloud DID routes to."""
    wanted = (
        "dial-rule-translation-destination-user",
        "dial_rule_translation_destination_user",
        "destination_user",
        "user",
        "subscriber",
    )
    for key in wanted:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _device_status(row: dict) -> dict:
    state = str(row.get("device-sip-registration-state") or "unknown").strip().lower()
    mac = str(row.get("device-provisioning-mac-address") or "").strip()
    raw_mac = "".join(ch for ch in mac if ch.isalnum()).upper()
    return {
        "device": str(row.get("device") or "").strip(),
        "model": str(row.get("device-models-model") or "").strip(),
        "mac": ":".join(raw_mac[i:i+2] for i in range(0, 12, 2)) if len(raw_mac) == 12 else mac,
        "state": state,
        "online": state == "registered",
        "server": str(row.get("core-server") or row.get("device-provisioning-registration-core-server") or "").strip(),
        "ip": str(row.get("device-sip-registration-ip-address") or "").strip(),
        "user_agent": str(row.get("device-sip-registration-user-agent") or "").strip(),
        "line": row.get("device-provisioning-line"),
    }


def _rate_for_crid(profile: dict, crid: str) -> dict | None:
    target = str(crid).strip()
    for rate in profile.get("rates") or []:
        if not isinstance(rate, dict):
            continue
        current = str(rate.get("crid") or rate.get("cr_id") or "").strip()
        if current == target:
            return rate
    return None


def _is_digital_voice_rate(rate: dict) -> bool:
    text = " ".join(str(rate.get(k) or "") for k in ("rg_name", "name", "rg_description")).lower()
    return any(token in text for token in ("digital voice", "digicloud", "voip", "phone"))


def _service_snapshot(service: CustomerService) -> dict:
    try:
        value = json.loads(service.source_snapshot_json or "{}")
    except (TypeError, ValueError):
        value = {}
    return value if isinstance(value, dict) else {}


def _format_phone_number(value: object) -> str:
    digits = _digits(value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return str(value or "").strip()


def _digicloud_subscriber_view(service: CustomerService) -> dict:
    snapshot = _service_snapshot(service)
    extension = str(
        snapshot.get("extension")
        or str(service.service_identifier or "").split("@", 1)[0]
    ).strip()
    domain = str(
        snapshot.get("domain")
        or (str(service.service_identifier).rsplit("@", 1)[1] if "@" in str(service.service_identifier) else "")
    ).strip()
    return {
        "service_id": service.id,
        "phone_number": _format_phone_number(extension),
        "extension": extension,
        "domain": domain,
        "status": service.status,
        "presence": str(snapshot.get("digicloud_presence") or "active"),
        "missing_checks": int(snapshot.get("consecutive_missing_checks") or 0),
        "first_name": str(snapshot.get("first_name") or "").strip(),
        "last_name": str(snapshot.get("last_name") or "").strip(),
        "email": str(snapshot.get("email") or "").strip(),
    }


def _is_plume_rate(rate: dict) -> bool:
    text = " ".join(str(rate.get(k) or "") for k in ("rg_name", "name", "rg_description")).lower()
    service_text = " ".join(
        str(service.get("s_name") or "")
        for service in (rate.get("services") or []) if isinstance(service, dict)
    ).lower()
    combined = f"{text} {service_text}"
    return any(token in combined for token in ("plume", "managed wi-fi", "managed wifi", "wifi pod", "wi-fi pod"))


def _looks_like_plume_identifier(value: object) -> bool:
    text = str(value or "").strip()
    compact = "".join(ch for ch in text if ch.isalnum())
    return (
        len(compact) in {10, 12, 24}
        and not compact.isdigit()
        and compact.isalnum()
    )


def _plume_identifier(service: dict) -> str:
    """Choose a real Plume node serial/location from a service record."""
    value = str(service.get("s_data") or "").strip()
    if _looks_like_plume_identifier(value):
        return value
    detail = service.get("detail") or {}
    if not isinstance(detail, dict):
        return ""
    preferred: list[str] = []
    fallback: list[str] = []
    for key, raw_value in detail.items():
        candidate = str(raw_value or "").strip()
        if not _looks_like_plume_identifier(candidate):
            continue
        normalized_key = "".join(ch for ch in str(key).lower() if ch.isalnum())
        if any(token in normalized_key for token in (
            "serial", "serialnumber", "nodeserial", "pod", "plume", "locationid",
        )):
            preferred.append(candidate)
        elif "mac" not in normalized_key:
            fallback.append(candidate)
    return (preferred or fallback or [""])[0]


def _is_plume_service(service: dict) -> bool:
    """Identify a service instance that can safely be resolved by Plume.

    A Plume-branded rate may also contain billing-only hardware such as an
    Adtran gateway. Numeric inventory values from those services must never be
    sent to the Plume node/location endpoints.
    """
    name = str(service.get("s_name") or "").strip().lower()
    named_for_plume = any(token in name for token in (
        "plume", "pod", "adtran gateway", "plume id", "location id", "subscriber id",
    ))
    return bool(_plume_identifier(service)) and named_for_plume


def _plume_service_id(rate: dict) -> str:
    preferred: list[str] = []
    for service in rate.get("services") or []:
        if not isinstance(service, dict) or not _is_plume_service(service):
            continue
        value = _plume_identifier(service)
        if value:
            preferred.append(value)
    return (preferred or [""])[0]


def _rate_dids(rate: dict) -> list[str]:
    values: list[str] = []
    for svc in rate.get("services") or []:
        if not isinstance(svc, dict):
            continue
        name = str(svc.get("s_name") or "").lower()
        data = _digits(svc.get("s_data"))
        if len(data) == 11 and data.startswith("1"):
            data = data[1:]
        if len(data) == 10 and ("did" in name or "phone" in name or "number" in name):
            values.append(data)
    return list(dict.fromkeys(values))



CUSTOMER_SEARCH_STATUSES = ("active", "on_hold", "suspended", "inactive")
DEFAULT_CUSTOMER_SEARCH_STATUSES = ("active", "on_hold")
STATUS_LABELS = {
    "active": "Active",
    "on_hold": "On Hold",
    "suspended": "Suspended",
    "inactive": "Inactive",
}
STATUS_BADGES = {
    "active": "text-bg-success",
    "on_hold": "text-bg-warning",
    "suspended": "text-bg-danger",
    "inactive": "text-bg-secondary",
}


def _normalize_customer_status(value: object) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "y": "active", "active": "active",
        "h": "on_hold", "hold": "on_hold", "on_hold": "on_hold", "onhold": "on_hold",
        "s": "suspended", "suspend": "suspended", "suspended": "suspended",
        "n": "inactive", "inactive": "inactive", "disabled": "inactive",
    }
    return mapping.get(raw, "inactive")


def _normalize_phone(value: object) -> str:
    digits = _digits(value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def _local_search_rows(request: Request, query: str, statuses: set[str]) -> list[dict]:
    """Search NOP operational customers while respecting organization scope."""
    context = context_from_request(request)
    with SessionLocal() as db:
        statement = select(Customer).options(
            selectinload(Customer.contacts),
            selectinload(Customer.external_links),
        )
        if not context.is_staff:
            statement = statement.where(
                or_(
                    Customer.owner_organization_id == context.organization_id,
                    Customer.servicing_organization_id == context.organization_id,
                )
            )
        customers = list(db.scalars(statement.limit(2000)).unique())

        term = query.strip().lower()
        rows: list[dict] = []
        for customer in customers:
            status = _normalize_customer_status(customer.status)
            if status not in statuses:
                continue
            searchable = [
                customer.name, customer.customer_number, customer.billing_email, customer.billing_phone,
            ]
            phones: list[str] = []
            emails: list[str] = []
            for contact in customer.contacts:
                searchable.extend([contact.full_name, contact.email, contact.office_phone, contact.mobile_phone])
                if contact.email:
                    emails.append(contact.email.strip().lower())
                for phone in (contact.office_phone, contact.mobile_phone):
                    normalized = _normalize_phone(phone)
                    if normalized:
                        phones.append(normalized)
            if customer.billing_email:
                emails.append(customer.billing_email.strip().lower())
            billing_phone = _normalize_phone(customer.billing_phone)
            if billing_phone:
                phones.append(billing_phone)
            if term and not any(term in str(value or "").lower() for value in searchable):
                # Also allow digit-only phone searches regardless of formatting.
                term_digits = _normalize_phone(term)
                if not term_digits or not any(term_digits in phone for phone in phones):
                    continue
            plat_link = next(
                (
                    link for link in customer.external_links
                    if link.system_name.lower() == "platypus" and link.record_type.lower() == "customer"
                ),
                None,
            )
            primary = customer.primary_contact
            sources = ["nop"]
            if plat_link is not None:
                # A durable external link proves this is a Platypus-backed NOP
                # customer even when the current live SearchCustomer response
                # omits the account (for example because of provider search
                # matching or result limits).
                sources.append("platypus")
            rows.append({
                "source": "nop",
                "sources": sources,
                "local_id": customer.id,
                "platypus_id": plat_link.external_id if plat_link else None,
                "id": plat_link.external_id if plat_link else str(customer.id),
                "name": customer.name,
                "attn": primary.full_name if primary else None,
                "phone": customer.billing_phone or (primary.office_phone if primary else "") or (primary.mobile_phone if primary else ""),
                "phonemasked": customer.billing_phone or (primary.office_phone if primary else "") or (primary.mobile_phone if primary else ""),
                "username": None,
                "status": status,
                "status_label": STATUS_LABELS[status],
                "status_badge": STATUS_BADGES[status],
                "phones_normalized": sorted(set(phones)),
                "emails_normalized": sorted(set(emails)),
                "open_url": f"/customers/{plat_link.external_id}" if plat_link else f"/customers/local/{customer.id}",
            })
        return rows


def _merge_customer_results(local_rows: list[dict], platypus_rows: list[dict], statuses: set[str]) -> list[dict]:
    """Merge Platypus + NOP search results without presenting linked customers twice.

    Exact external links win. For older NOP rows without an external link, a unique
    normalized phone match is used as a conservative fallback. Name-only matching is
    intentionally avoided because it can merge different people with the same name.
    """
    by_plat_id = {str(row.get("platypus_id")): row for row in local_rows if row.get("platypus_id")}
    phone_to_local: dict[str, list[dict]] = {}
    for row in local_rows:
        for phone in row.get("phones_normalized") or []:
            phone_to_local.setdefault(phone, []).append(row)

    consumed_local: set[int] = set()
    merged: list[dict] = []
    for raw in platypus_rows:
        status = _normalize_customer_status(raw.get("active") or raw.get("activestatus"))
        if status not in statuses:
            continue
        plat_id = str(raw.get("id") or "").strip()
        phone = _normalize_phone(raw.get("phone") or raw.get("phonemasked"))
        local = by_plat_id.get(plat_id)
        if local is None and phone:
            candidates = [row for row in phone_to_local.get(phone, []) if row.get("local_id") not in consumed_local]
            if len(candidates) == 1:
                local = candidates[0]
        row = {
            "source": "platypus",
            "sources": ["platypus"],
            "local_id": None,
            "platypus_id": plat_id,
            "id": plat_id,
            "name": raw.get("name"),
            "attn": raw.get("attn"),
            "phone": raw.get("phone"),
            "phonemasked": raw.get("phonemasked"),
            "username": raw.get("username"),
            "status": status,
            "status_label": STATUS_LABELS[status],
            "status_badge": STATUS_BADGES[status],
            "open_url": f"/customers/{plat_id}",
        }
        if local is not None:
            consumed_local.add(int(local["local_id"]))
            row["sources"] = ["nop", "platypus"]
            row["local_id"] = local["local_id"]
            # Prefer live Platypus status and identity, but fill blanks from NOP.
            for key in ("name", "attn", "phone", "phonemasked"):
                if not row.get(key):
                    row[key] = local.get(key)
        merged.append(row)

    for row in local_rows:
        if row.get("local_id") in consumed_local:
            continue
        merged.append(row)

    merged.sort(key=lambda item: (str(item.get("name") or "").lower(), str(item.get("id") or "")))
    return merged


@router.get("")
async def customer_search(
    request: Request,
    q: str = Query(""),
    status: list[str] | None = Query(default=None),
):
    require_permission(request, "customers.read")
    selected_statuses = {
        value for value in (status or DEFAULT_CUSTOMER_SEARCH_STATUSES)
        if value in CUSTOMER_SEARCH_STATUSES
    }
    if not selected_statuses:
        selected_statuses = set(DEFAULT_CUSTOMER_SEARCH_STATUSES)

    matches: list[dict] = []
    error = None
    if q.strip():
        local_rows = _local_search_rows(request, q, selected_statuses)
        try:
            platypus_rows = await _directory().search(q)
        except PlatypusError as exc:
            # NOP search remains usable if Platypus is temporarily unavailable.
            platypus_rows = []
            error = f"Platypus search unavailable: {exc}"
        matches = _merge_customer_results(local_rows, platypus_rows, selected_statuses)

    return render(
        request,
        "customers/index.html",
        q=q,
        customers=matches,
        error=error,
        selected_statuses=selected_statuses,
        status_labels=STATUS_LABELS,
        status_options=CUSTOMER_SEARCH_STATUSES,
        active_path="/customers",
    )


@router.get("/local/{local_customer_id}")
async def local_customer_detail(request: Request, local_customer_id: int):
    require_permission(request, "customers.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        statement = select(Customer).options(
            selectinload(Customer.contacts),
            selectinload(Customer.locations),
            selectinload(Customer.services),
            selectinload(Customer.external_links),
        ).where(Customer.id == local_customer_id)
        if not context.is_staff:
            statement = statement.where(
                or_(
                    Customer.owner_organization_id == context.organization_id,
                    Customer.servicing_organization_id == context.organization_id,
                )
            )
        customer = db.scalar(statement)
        if customer is None:
            raise HTTPException(status_code=404, detail="NOP customer not found")
        # If this customer is already linked to Platypus, use the live profile.
        if customer.platypus_link:
            return_to = customer.platypus_link.external_id
        else:
            return_to = None
        # Touch eagerly-loaded relationships before leaving the session.
        _ = list(customer.contacts), list(customer.locations), list(customer.services), list(customer.external_links)
        db.expunge(customer)
    if return_to:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/customers/{return_to}", status_code=303)
    return render(
        request,
        "customers/local_detail.html",
        customer=customer,
        active_path="/customers",
    )


@router.get("/local/{local_customer_id}/duplicate")
async def manage_duplicate_customer(
    request: Request,
    local_customer_id: int,
    target_id: int | None = Query(default=None),
    error: str = Query(default=""),
    notice: str = Query(default=""),
):
    context = require_platform_staff(request)
    with SessionLocal() as db:
        service = CustomerMergeService(db, context)
        try:
            preview = service.preview(local_customer_id, target_id)
            candidates = service.candidates(local_customer_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        source_link = preview.source.platypus_link
        return_url = (
            f"/customers/{source_link.external_id}" if source_link
            else f"/customers/local/{preview.source.id}"
        )
        return render(
            request,
            "customers/manage_duplicate.html",
            source=preview.source,
            target=preview.target,
            candidates=candidates,
            counts=preview.counts,
            conflicts=preview.conflicts,
            can_delete=preview.can_delete,
            delete_blockers=preview.delete_blockers,
            return_url=return_url,
            error=error,
            notice=notice,
            active_path="/customers",
        )


@router.post("/local/{local_customer_id}/merge")
async def merge_duplicate_customer(
    request: Request,
    local_customer_id: int,
    target_id: int = Form(...),
    confirmation: str = Form(...),
):
    context = require_platform_staff(request)
    back = f"/customers/local/{local_customer_id}/duplicate?target_id={target_id}"
    if confirmation.strip().upper() != "MERGE":
        return RedirectResponse(f"{back}&error={quote_plus('Type MERGE to confirm.')}", status_code=303)
    with SessionLocal() as db:
        service = CustomerMergeService(db, context)
        try:
            source = service._customer(local_customer_id)
            target = service._customer(target_id)
            source_name, target_name = source.name, target.name
            counts = service.merge(local_customer_id, target_id)
            AuditService(db, request, context).record(
                "customers.merge",
                "customer",
                target_id,
                f"Merged duplicate NOP customer {source_name} #{local_customer_id} into {target_name} #{target_id}.",
                module="customers",
                event_data={"source_customer_id": local_customer_id, "target_customer_id": target_id, "moved": counts},
            )
            db.commit()
        except (ValueError, PermissionError, SQLAlchemyError) as exc:
            db.rollback()
            detail = str(getattr(exc, "orig", exc))
            return RedirectResponse(
                f"{back}&error={quote_plus('Merge could not be completed: ' + detail)}",
                status_code=303,
            )
    return RedirectResponse(
        f"/customers/local/{target_id}?notice={quote_plus('Duplicate customer merged successfully.')}",
        status_code=303,
    )


@router.post("/local/{local_customer_id}/delete")
async def delete_duplicate_customer(
    request: Request,
    local_customer_id: int,
    confirmation: str = Form(...),
):
    context = require_platform_staff(request)
    back = f"/customers/local/{local_customer_id}/duplicate"
    if confirmation.strip().upper() != "DELETE":
        return RedirectResponse(f"{back}?error={quote_plus('Type DELETE to confirm.')}", status_code=303)
    with SessionLocal() as db:
        service = CustomerMergeService(db, context)
        try:
            source = service.delete_unused(local_customer_id)
            AuditService(db, request, context).record(
                "customers.delete_duplicate",
                "customer",
                local_customer_id,
                f"Deleted unused duplicate NOP customer {source.name} #{local_customer_id}.",
                module="customers",
                event_data={"deleted_customer_id": local_customer_id, "customer_number": source.customer_number},
            )
            db.commit()
        except (ValueError, PermissionError, SQLAlchemyError) as exc:
            db.rollback()
            detail = str(getattr(exc, "orig", exc))
            return RedirectResponse(
                f"{back}?error={quote_plus('Customer could not be deleted: ' + detail)}",
                status_code=303,
            )
    return RedirectResponse("/customers?notice=Duplicate+customer+deleted", status_code=303)


@router.get("/{customer_id}")
async def customer_detail(request: Request, customer_id: str):
    try:
        profile = await _directory().get(customer_id)
    except PlatypusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not profile.get("customer"):
        raise HTTPException(status_code=404, detail="Platypus customer not found")
    require_permission(request, "customers.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        try:
            local_customer = PlatypusCustomerSync(db, context).sync(profile)
            db.commit()
            local_customer_id = local_customer.id
            recent_tickets = list(db.scalars(select(Ticket).where(Ticket.customer_id == local_customer_id).order_by(Ticket.created_at.desc()).limit(5)).unique())
            recent_jobs = list(db.scalars(select(Job).where(Job.customer_id == local_customer_id).order_by(Job.created_at.desc()).limit(5)).unique())
            recent_estimates = list(db.scalars(select(Estimate).where(Estimate.customer_id == local_customer_id).order_by(Estimate.created_at.desc()).limit(5)).unique())
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Unable to synchronize this Platypus customer into NOP: {exc}") from exc
    profile["local_customer_id"] = local_customer_id
    profile["display_phones"] = _customer_phone_numbers(profile)
    for rate in profile.get("rates", []):
        rate["is_plume"] = _is_plume_rate(rate)
        rate["plume_service_id"] = _plume_service_id(rate) if rate["is_plume"] else ""
        for service in rate.get("services") or []:
            if isinstance(service, dict):
                service["is_plume"] = _is_plume_service(service)
                service["plume_service_id"] = _plume_identifier(service)
    profile_plume_service_id = next(
        (
            str(rate.get("plume_service_id") or "").strip()
            for rate in profile.get("rates", [])
            if isinstance(rate, dict) and rate.get("plume_service_id")
        ),
        "",
    )
    return render(
        request,
        "customers/detail.html",
        profile=profile,
        customer=profile["customer"],
        local_customer_id=local_customer_id,
        recent_tickets=recent_tickets,
        recent_jobs=recent_jobs,
        recent_estimates=recent_estimates,
        profile_plume_service_id=profile_plume_service_id,
        active_path="/customers",
    )


@router.get("/{customer_id}/rates/{crid:int}")
async def customer_rate_service_status(request: Request, customer_id: str, crid: int):
    require_permission(request, "customers.read")
    try:
        profile = await _directory().get(customer_id)
    except PlatypusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not profile.get("customer"):
        raise HTTPException(status_code=404, detail="Platypus customer not found")

    crid = str(crid)
    rate = _rate_for_crid(profile, crid)
    if rate is None:
        raise HTTPException(status_code=404, detail="Customer rate not found")

    links: list[dict] = []
    live_error = None
    is_plume = _is_plume_rate(rate)
    plume_snapshot = None
    plume_service_id = _plume_service_id(rate)
    local_customer_id = None
    if is_plume:
        with SessionLocal() as db:
            plat_link = db.scalar(select(ExternalRecordLink).where(
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
                ExternalRecordLink.external_id == str(profile["platypus_customer_id"]),
            ))
            if plat_link is not None:
                local_customer_id = plat_link.customer_id
                network = db.scalar(select(PlumeCustomerNetwork).where(
                    PlumeCustomerNetwork.customer_id == local_customer_id
                ))
            else:
                network = None
        if local_customer_id:
            return RedirectResponse(
                f"/customers/{local_customer_id}/plume"
                f"?service_id={quote_plus(plume_service_id)}",
                status_code=303,
            )
        try:
            plume_snapshot = PlumeReadService().snapshot(
                service_id=plume_service_id,
                customer_id=(network.plume_customer_id if network else ""),
                location_id=(network.plume_location_id if network else ""),
            )
        except (PlumeError, ValueError) as exc:
            live_error = f"Unable to read Plume status: {exc}"
    if _is_digital_voice_rate(rate):
        context = context_from_request(request)
        with SessionLocal() as db:
            visible_domains = {d.domain_name.lower(): d for d in DigiCloudService(db, context, request).list_domains()}
            for did in _rate_dids(rate):
                local_number = db.scalar(select(DigiCloudPhoneNumber).where(DigiCloudPhoneNumber.telephone_number == did))
                item = {
                    "did": did, "linked": False, "domain": "", "username": "",
                    "user": None, "devices": [], "rules": [], "error": None,
                    "emergency_address": {}, "emergency_address_error": None,
                    "emergency_address_source": "none",
                    "emergency_provisioned": False,
                    "emergency_did_matches": False,
                    "emergency_did_configured": False,
                    "emergency_endpoint_found": False,
                    "emergency_provisioned_carrier": "",
                    "user_emergency_did": "",
                }
                if local_number is None or local_number.domain is None:
                    item["error"] = "This DID is not linked to a DigiCloud domain in NOP inventory."
                    links.append(item)
                    continue
                domain = local_number.domain.domain_name
                item["domain"] = domain
                if domain.lower() not in visible_domains:
                    item["error"] = "This DigiCloud domain is outside your allowed domain scope."
                    links.append(item)
                    continue
                try:
                    number_row = NetSapiensPhoneNumbers().get_for_domain(domain, did)
                    username = _destination_user(number_row)
                    item["username"] = username
                    if not username:
                        item["error"] = "The DID exists in DigiCloud but is not routed to a user."
                    else:
                        user_profile = NetSapiensUsers().get(domain, username)
                        if user_profile.get("hidden"):
                            item["error"] = "The linked DigiCloud user is protected/hidden."
                        else:
                            devices = [_device_status(row) for row in NetSapiensDevices().list(domain, username)]
                            rules, _ = NetSapiensAnsweringRules().list(domain, username)
                            emergency_address = {}
                            emergency_address_error = None
                            emergency_address_source = "none"
                            user_emergency_did = _digits(
                                user_profile.get("emergency_caller_id")
                            )[-10:]
                            expected_did = _digits(did)[-10:]
                            emergency_did_configured = bool(
                                user_profile.get("emergency_caller_id_configured")
                            )
                            emergency_did_matches = (
                                emergency_did_configured
                                and len(user_emergency_did) == 10
                                and user_emergency_did == expected_did
                            )
                            emergency_provisioned = False
                            emergency_endpoint_found = False
                            emergency_provisioned_carrier = ""
                            if request.state.user.can("digicloud.users.manage"):
                                try:
                                    emergency_address = NetSapiensEmergencyAddresses().endpoint_for_did(
                                        domain, expected_did
                                    )
                                    emergency_endpoint_found = bool(
                                        emergency_address.get("callback_number")
                                    )
                                    emergency_provisioned_carrier = str(
                                        emergency_address.get("provisioned_carrier") or ""
                                    ).strip()
                                    if emergency_endpoint_found:
                                        emergency_address_source = "digicloud_endpoint"
                                        # The API confirms the endpoint record,
                                        # not completion at the 911 carrier.
                                        emergency_provisioned = False
                                except NetSapiensError as exc:
                                    emergency_address_error = str(exc).replace("NetSapiens", "DigiCloud")
                                if emergency_address_source != "digicloud_endpoint":
                                    mapped_service = db.scalar(select(CustomerService).where(
                                        CustomerService.source_system == "digicloud",
                                        CustomerService.service_identifier == f"{username}@{domain}",
                                    ))
                                    if mapped_service is not None:
                                        fallback = _service_snapshot(mapped_service).get("legacy_911_address")
                                        if isinstance(fallback, dict) and fallback.get("address_line_1"):
                                            emergency_address = fallback
                                            emergency_address_source = "nop_snapshot"
                            item.update({
                                "linked": True,
                                "user": user_profile,
                                "devices": devices,
                                "rules": rules,
                                "online_devices": sum(1 for d in devices if d["online"]),
                                "emergency_address": emergency_address,
                                "emergency_address_error": emergency_address_error,
                                "emergency_address_source": emergency_address_source,
                                "emergency_provisioned": emergency_provisioned,
                                "emergency_did_matches": emergency_did_matches,
                                "emergency_did_configured": emergency_did_configured,
                                "emergency_endpoint_found": emergency_endpoint_found,
                                "emergency_provisioned_carrier": emergency_provisioned_carrier,
                                "user_emergency_did": user_emergency_did,
                            })
                except NetSapiensError as exc:
                    item["error"] = str(exc).replace("NetSapiens", "DigiCloud")
                except Exception as exc:
                    item["error"] = f"Unable to read DigiCloud service status: {exc}"
                links.append(item)
    for rate in profile.get("rates") or []:
        if isinstance(rate, dict):
            rate["is_plume"] = _is_plume_rate(rate)
            rate["plume_service_id"] = _plume_service_id(rate) if rate["is_plume"] else ""
    return render(
        request,
        "customers/rate_status.html",
        profile=profile, customer=profile["customer"], rate=rate, crid=crid,
        is_digital_voice=_is_digital_voice_rate(rate), digicloud_links=links,
        is_plume=is_plume, plume_snapshot=plume_snapshot,
        plume_service_id=plume_service_id, local_customer_id=local_customer_id,
        live_error=live_error,
        active_path="/customers",
    )


@router.get("/{customer_id}/rates/manage")
async def customer_manage_rates(request: Request, customer_id: str, message: str = "", error: str = ""):
    require_permission(request, "customers.read")
    require_platform_staff(request)
    client = PlatypusClient()
    try:
        profile = await CustomerDirectory(client).get(customer_id)
        customer = profile.get("customer") or {}
        if not customer:
            raise HTTPException(status_code=404, detail="Platypus customer not found")
        store_id = str(customer.get("storeid") or customer.get("store_id") or "").strip()
        if not store_id:
            raise ValueError("Platypus did not return this customer's store ID.")
        available = await client.get_available_web_rates(customer_id, store_id)
        context = context_from_request(request)
        with SessionLocal() as db:
            local = PlatypusCustomerSync(db, context).sync(profile)
            db.commit()
            profile["local_customer_id"] = local.id
            plume_network = db.scalar(select(PlumeCustomerNetwork).where(
                PlumeCustomerNetwork.customer_id == local.id
            ))
            has_plume_network = bool(
                plume_network
                and (plume_network.plume_customer_id or plume_network.plume_location_id)
            )
            digicloud_services = list(db.scalars(select(CustomerService).where(
                CustomerService.customer_id == local.id,
                CustomerService.source_system == "digicloud",
            )).all())
        digicloud_by_crid: dict[str, list[dict]] = {}
        for service in digicloud_services:
            crid = str(service.source_rate_id or _service_snapshot(service).get("crid") or "").strip()
            if crid:
                digicloud_by_crid.setdefault(crid, []).append(
                    _digicloud_subscriber_view(service)
                )
        for rate in profile.get("rates") or []:
            if isinstance(rate, dict):
                rate["is_plume"] = _is_plume_rate(rate)
                rate["is_digital_voice"] = _is_digital_voice_rate(rate)
                rate["plume_service_id"] = _plume_service_id(rate) if rate["is_plume"] else ""
                rate_crid = str(rate.get("crid") or rate.get("cr_id") or "").strip()
                rate["digicloud_subscribers"] = digicloud_by_crid.get(rate_crid, [])
    except PlatypusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # GetAvailableWebRates may return one row per frequency. Show every valid
    # billing choice, but suppress exact duplicate RGID/frequency rows.
    options: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in available:
        rgid = str(row.get("rg_id") or row.get("rgid") or row.get("id") or "").strip()
        frequency = str(row.get("r_frequency") or "1").strip()
        if not rgid or (rgid, frequency) in seen:
            continue
        seen.add((rgid, frequency))
        options.append({
            "rgid": rgid,
            "name": str(row.get("rg_name") or row.get("name") or f"Rate {rgid}"),
            "description": str(row.get("rg_description") or ""),
            "frequency": frequency,
            "price": str(row.get("rg_fixed_price") or ""),
            "plume_role": (
                "extender" if "extender" in str(row.get("rg_name") or row.get("name") or "").lower()
                else "gateway" if _is_plume_rate(row)
                else ""
            ),
            "digicloud_role": "subscriber" if rgid in {"249", "98", "99"} else "",
        })
    options.sort(key=lambda item: (item["name"].lower(), item["frequency"]))
    return render(
        request,
        "customers/manage_rates.html",
        profile=profile,
        customer=customer,
        assigned_rates=profile.get("rates") or [],
        available_rates=options,
        has_plume_network=has_plume_network,
        message=message,
        error=error,
        active_path="/customers",
    )


def _customer_digicloud_service(db, customer_id: str, service_id: int) -> tuple[CustomerService, ExternalRecordLink]:
    link = db.scalar(select(ExternalRecordLink).where(
        ExternalRecordLink.system_name == "platypus",
        ExternalRecordLink.record_type == "customer",
        ExternalRecordLink.external_id == str(customer_id),
    ))
    if link is None:
        raise ValueError("The Platypus customer is not linked to a NOP customer.")
    service = db.scalar(select(CustomerService).where(
        CustomerService.id == service_id,
        CustomerService.customer_id == link.customer_id,
        CustomerService.source_system == "digicloud",
    ))
    if service is None:
        raise ValueError("The DigiCloud billing link was not found for this customer.")
    return service, link


@router.post("/{customer_id}/rates/reconcile-digicloud")
async def customer_reconcile_digicloud(request: Request, customer_id: str):
    require_permission(request, "customers.read")
    require_platform_staff(request)
    try:
        with SessionLocal() as db:
            link = db.scalar(select(ExternalRecordLink).where(
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
                ExternalRecordLink.external_id == str(customer_id),
            ))
            if link is None:
                raise ValueError("The Platypus customer is not linked to a NOP customer.")
            services = list(db.scalars(select(CustomerService).where(
                CustomerService.customer_id == link.customer_id,
                CustomerService.source_system == "digicloud",
                CustomerService.status.in_({
                    "active", "missing_from_digicloud", "external_delete_ignored",
                    "billing_cleanup_required",
                }),
            )).all())
            domains = sorted({
                str(_service_snapshot(service).get("domain") or "").strip().lower()
                or (
                    str(service.service_identifier).rsplit("@", 1)[1].strip().lower()
                    if "@" in str(service.service_identifier) else ""
                )
                for service in services
            } - {""})
            if not domains:
                raise ValueError("No DigiCloud subscribers are linked to this customer.")
            totals = {"checked": 0, "pending": 0, "missing": 0, "restored": 0}
            for domain in domains:
                # Only a successful inventory read is allowed to affect state.
                live_users = NetSapiensUsers().list(domain)
                result = reconcile_domain(
                    db,
                    domain,
                    live_users,
                    confirmations=get_settings().digicloud_user_reconcile_confirmations,
                    customer_id=link.customer_id,
                )
                for key in totals:
                    totals[key] += result[key]
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.reconcile", "customer", link.customer_id,
                f"Reconciled {totals['checked']} DigiCloud billing link(s).",
                module="digicloud",
                event_data={"platypus_customer_id": customer_id, **totals, "domains": domains},
            )
            db.commit()
    except (ValueError, NetSapiensError) as exc:
        return RedirectResponse(
            f"/customers/{customer_id}/rates/manage?error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
            status_code=303,
        )
    message = (
        f"DigiCloud reconciliation complete: {totals['checked']} checked, "
        f"{totals['missing']} missing, {totals['restored']} restored."
    )
    if totals["pending"]:
        message += f" {totals['pending']} absence(s) require another successful check."
    return RedirectResponse(
        f"/customers/{customer_id}/rates/manage?message={quote_plus(message)}",
        status_code=303,
    )


@router.post("/{customer_id}/rates/digicloud/{service_id}/ignore")
async def customer_ignore_missing_digicloud_user(
    request: Request, customer_id: str, service_id: int
):
    require_permission(request, "customers.read")
    require_platform_staff(request)
    try:
        with SessionLocal() as db:
            service, link = _customer_digicloud_service(db, customer_id, service_id)
            if service.status != "missing_from_digicloud":
                raise ValueError("Only a confirmed missing DigiCloud subscriber can be ignored.")
            snapshot = _service_snapshot(service)
            snapshot["external_delete_ignored_at"] = datetime.now(timezone.utc).isoformat()
            snapshot["digicloud_presence"] = "missing_ignored"
            service.source_snapshot_json = json.dumps(snapshot, default=str, sort_keys=True)
            service.status = "external_delete_ignored"
            service.notes = "External DigiCloud deletion acknowledged; billing retained by staff."
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.external_delete_ignored", "customer_service", service.id,
                service.notes, module="digicloud", organization_id=service.customer.owner_organization_id,
                event_data={"platypus_customer_id": customer_id, "crid": service.source_rate_id},
            )
            db.commit()
    except ValueError as exc:
        return RedirectResponse(
            f"/customers/{customer_id}/rates/manage?error={quote_plus(str(exc))}", status_code=303
        )
    return RedirectResponse(
        f"/customers/{customer_id}/rates/manage?message={quote_plus('The external deletion was acknowledged and billing was retained.')}",
        status_code=303,
    )


@router.post("/{customer_id}/rates/digicloud/{service_id}/remove-billing")
async def customer_remove_missing_digicloud_billing(
    request: Request,
    customer_id: str,
    service_id: int,
    confirmation: str = Form(""),
):
    require_permission(request, "customers.read")
    require_platform_staff(request)
    client = PlatypusClient()
    try:
        with SessionLocal() as db:
            service, link = _customer_digicloud_service(db, customer_id, service_id)
            if service.status not in {
                "missing_from_digicloud", "external_delete_ignored", "billing_cleanup_required"
            }:
                raise ValueError("Billing can only be removed for a missing DigiCloud subscriber.")
            subscriber = _digicloud_subscriber_view(service)
            expected = f"REMOVE {subscriber['extension']}"
            if confirmation.strip().upper() != expected.upper():
                raise ValueError(f"Type {expected} exactly to confirm billing removal.")
            crid = str(service.source_rate_id or _service_snapshot(service).get("crid") or "").strip()
            if not crid:
                raise ValueError("The DigiCloud service does not have a linked Platypus CRID.")
            await client.delete_rate(customer_id, crid)
            service.status = "cancelled"
            service.cancellation_date = date.today()
            service.notes = "Missing DigiCloud subscriber billing was removed from Platypus."
            snapshot = _service_snapshot(service)
            snapshot.update({
                "billing_status": "removed",
                "billing_removed_at": datetime.now(timezone.utc).isoformat(),
                "digicloud_presence": "missing",
            })
            service.source_snapshot_json = json.dumps(snapshot, default=str, sort_keys=True)
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.missing_billing_removed", "customer_service", service.id,
                f"Removed Platypus CRID {crid} for missing DigiCloud subscriber {subscriber['extension']}.",
                module="digicloud", organization_id=service.customer.owner_organization_id,
                event_data={
                    "platypus_customer_id": customer_id, "crid": crid,
                    "domain": subscriber["domain"], "extension": subscriber["extension"],
                },
            )
            db.commit()
    except (ValueError, PlatypusError) as exc:
        return RedirectResponse(
            f"/customers/{customer_id}/rates/manage?error={quote_plus(str(exc))}", status_code=303
        )
    return RedirectResponse(
        f"/customers/{customer_id}/rates/manage?message={quote_plus(f'Removed Platypus CRID {crid} for the missing DigiCloud subscriber.')}",
        status_code=303,
    )


@router.post("/{customer_id}/rates/manage/add")
async def customer_add_rate(
    request: Request,
    customer_id: str,
    rate_selection: str = Form(""),
    quantity: int = Form(1),
    confirmation: str = Form(""),
    serial_number: str = Form(""),
    pod_name: str = Form(""),
):
    require_permission(request, "customers.read")
    require_platform_staff(request)
    if confirmation.strip().upper() != "ADD RATE":
        raise HTTPException(status_code=400, detail="Type ADD RATE to confirm.")
    try:
        rgid, frequency, rate_role = rate_selection.split(":", 2)
        if not rgid.strip() or int(frequency) < 1 or rate_role not in {"", "gateway", "extender", "digicloud"}:
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Choose a valid Platypus rate.")
    client = PlatypusClient()
    try:
        profile = await CustomerDirectory(client).get(customer_id)
        customer = profile.get("customer") or {}
        store_id = str(customer.get("storeid") or "").strip()
        available = await client.get_available_web_rates(customer_id, store_id)
        valid = any(
            str(row.get("rg_id") or row.get("rgid") or row.get("id") or "").strip() == rgid
            and str(row.get("r_frequency") or "1").strip() == frequency
            for row in available
        )
        if not valid:
            raise ValueError("The selected rate is no longer available to this customer.")
        if rate_role == "digicloud":
            return RedirectResponse(
                "/digicloud/users/new?"
                + urlencode({
                    "domain": "ntinet.com",
                    "platypus_customer_id": customer_id,
                    "rate_group_id": rgid,
                    "return_to": f"/customers/{customer_id}/rates/manage",
                }),
                status_code=303,
            )
        if rate_role in {"gateway", "extender"}:
            if not serial_number.strip() or not pod_name.strip():
                raise ValueError("Pod ID/serial and pod name are required for a Plume rate.")
            context = context_from_request(request)
            with SessionLocal() as db:
                local = PlatypusCustomerSync(db, context).sync(profile)
                db.commit()
                local_customer_id = local.id
            # Preserve the submitted fields. The Plume claim route performs the
            # claim and replays the same form into the existing rate/service
            # creation workflow; no duplicate AddRate call occurs here.
            return RedirectResponse(
                f"/customers/{local_customer_id}/plume/pods/add",
                status_code=307,
            )
        crid = await client.add_rate(customer_id, rgid, frequency=int(frequency), quantity=max(quantity, 1))
        refreshed = await CustomerDirectory(client).get(customer_id)
        context = context_from_request(request)
        with SessionLocal() as db:
            local = PlatypusCustomerSync(db, context).sync(refreshed)
            AuditService(db, request, context).record(
                "platypus.rate_added", "customer", local.id,
                f"Added Platypus RGID {rgid} as CRID {crid}.",
                module="customer-management", organization_id=local.owner_organization_id,
                event_data={"platypus_customer_id": customer_id, "rgid": rgid, "crid": crid, "frequency": frequency, "quantity": max(quantity, 1)},
            )
            db.commit()
    except (PlatypusError, ValueError) as exc:
        return RedirectResponse(f"/customers/{customer_id}/rates/manage?error={quote_plus(str(exc))}", status_code=303)
    return RedirectResponse(f"/customers/{customer_id}/rates/manage?message={quote_plus(f'Rate added successfully as CRID {crid}.')}", status_code=303)


@router.post("/{customer_id}/rates/{crid}/delete")
async def customer_delete_rate(
    request: Request,
    customer_id: str,
    crid: str,
    confirmation: str = Form(""),
    no_closeout: bool = Form(False),
):
    require_permission(request, "customers.read")
    require_platform_staff(request)
    if confirmation.strip().upper() != f"DELETE {crid}".upper():
        return RedirectResponse(
            f"/customers/{customer_id}/rates/manage?error="
            f"{quote_plus(f'Delete confirmation was not accepted for CRID {crid}. Please try again.')}",
            status_code=303,
        )
    client = PlatypusClient()
    plume_nodes_removed: list[str] = []
    try:
        before = await CustomerDirectory(client).get(customer_id)
        rate = _rate_for_crid(before, crid)
        if rate is None:
            raise ValueError("That customer rate no longer exists.")
        rate_name = str(rate.get("rg_name") or rate.get("name") or f"CRID {crid}")
        if _is_plume_rate(rate):
            service_identifiers = {
                _plume_identifier(service)
                for service in (rate.get("services") or [])
                if isinstance(service, dict) and _plume_identifier(service)
            }
            if service_identifiers:
                normalized_service_ids = {
                    "".join(ch for ch in value if ch.isalnum()).upper()
                    for value in service_identifiers
                }
                with SessionLocal() as db:
                    link = db.scalar(select(ExternalRecordLink).where(
                        ExternalRecordLink.system_name == "platypus",
                        ExternalRecordLink.record_type == "customer",
                        ExternalRecordLink.external_id == str(customer_id),
                    ))
                    network = db.scalar(select(PlumeCustomerNetwork).where(
                        PlumeCustomerNetwork.customer_id == link.customer_id
                    )) if link else None
                if not network or not network.plume_customer_id or not network.plume_location_id:
                    raise ValueError(
                        "This Plume rate has hardware services, but NOP does not have the Plume customer/location IDs required to unclaim them. The rate was not deleted."
                    )
                snapshot = PlumeReadService().snapshot(
                    service_id=_plume_service_id(rate),
                    customer_id=network.plume_customer_id,
                    location_id=network.plume_location_id,
                )
                matched_nodes: list[str] = []
                for pod in snapshot.get("pods") or []:
                    aliases = {
                        "".join(ch for ch in str(pod.get(key) or "") if ch.isalnum()).upper()
                        for key in ("id", "serial_number", "mac_address")
                    }
                    if aliases & normalized_service_ids:
                        node_id = str(pod.get("id") or pod.get("serial_number") or "").strip()
                        if node_id and node_id not in matched_nodes:
                            matched_nodes.append(node_id)
                if not matched_nodes:
                    raise ValueError(
                        "NOP could not match the Plume service on this rate to hardware at the customer's current Plume location. The rate was not deleted."
                    )
                provisioner = PlumeProvisioningService()
                for node_id in matched_nodes:
                    provisioner.unclaim_node(
                        customer_id=network.plume_customer_id,
                        location_id=network.plume_location_id,
                        node_id=node_id,
                    )
                    plume_nodes_removed.append(node_id)
        await client.delete_rate(customer_id, crid, no_closeout=no_closeout)
        refreshed = await CustomerDirectory(client).get(customer_id)
        context = context_from_request(request)
        with SessionLocal() as db:
            local = PlatypusCustomerSync(db, context).sync(refreshed)
            AuditService(db, request, context).record(
                "platypus.rate_deleted", "customer", local.id,
                f"Deleted Platypus rate {rate_name} (CRID {crid}).",
                module="customer-management", organization_id=local.owner_organization_id,
                event_data={"platypus_customer_id": customer_id, "crid": crid, "rate_name": rate_name, "no_closeout": no_closeout, "plume_nodes_unclaimed": plume_nodes_removed},
            )
            db.commit()
    except (PlatypusError, PlumeError, ValueError) as exc:
        detail = str(exc)
        if plume_nodes_removed:
            detail = (
                f"Plume hardware was unclaimed, but Platypus rate CRID {crid} could not be deleted. "
                f"Retry the rate deletion. Error: {detail}"
            )
        return RedirectResponse(f"/customers/{customer_id}/rates/manage?error={quote_plus(detail)}", status_code=303)
    result = f"Rate CRID {crid} deleted."
    if plume_nodes_removed:
        result = f"Unclaimed {len(plume_nodes_removed)} Plume device(s) and deleted rate CRID {crid}."
    return RedirectResponse(f"/customers/{customer_id}/rates/manage?message={quote_plus(result)}", status_code=303)


@api_router.get("/search")
async def api_customer_search(
    request: Request,
    q: str = Query(..., min_length=1),
    status: list[str] | None = Query(default=None),
):
    require_permission(request, "customers.read")
    selected_statuses = {
        value for value in (status or DEFAULT_CUSTOMER_SEARCH_STATUSES)
        if value in CUSTOMER_SEARCH_STATUSES
    } or set(DEFAULT_CUSTOMER_SEARCH_STATUSES)
    local_rows = _local_search_rows(request, q, selected_statuses)
    try:
        platypus_rows = await _directory().search(q)
    except PlatypusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "source": "unified",
        "statuses": sorted(selected_statuses),
        "customers": _merge_customer_results(local_rows, platypus_rows, selected_statuses),
    }


@api_router.get("/{customer_id}")
async def api_customer_detail(customer_id: str):
    try:
        profile = await _directory().get(customer_id)
    except PlatypusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not profile.get("customer"):
        raise HTTPException(status_code=404, detail="Platypus customer not found")
    return profile
