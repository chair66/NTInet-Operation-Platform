from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.database import SessionLocal
from app.database.customer_models import Customer, PlumeCustomerNetwork
from app.providers.plume import PlumeError
from app.providers.plume.client import plume_client
from app.security import context_from_request, require_permission
from app.services import AuditService
from app.services.customer_service import CustomerService
from app.services.notifications import render_email_template, send_email
from app.services.plume_read_service import PlumeReadService
from app.services.plume_provisioning_service import PlumeProvisioningService
from app.services.customer_directory import CustomerDirectory
from app.services.platypus import PlatypusClient, PlatypusError
from app.services.platypus_customer_sync import PlatypusCustomerSync
from app.web import render


router = APIRouter(prefix="/customers", tags=["Plume"])

# Platypus staff API logins can return DATA_ERROR from GetAvailableRates even
# when the rate is assignable. NTInet's confirmed Pod Extender RGID is 298.
PLATYPUS_POD_EXTENDER_RATE = {"id": "298", "name": "Pod Extender", "role": "extender"}


def _customer_or_404(db, request: Request, customer_id: int) -> Customer:
    context = context_from_request(request)
    customer = CustomerService(db, context).get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _plume_customer_hint(customer: Customer, network: PlumeCustomerNetwork | None) -> str:
    """Use a saved native Plume ID, otherwise try the Platypus ID as accountId."""
    if network and str(network.plume_customer_id or "").strip():
        return str(network.plume_customer_id).strip()
    if customer.platypus_link:
        return str(customer.platypus_link.external_id or "").strip()
    return ""


def _redirect(customer_id: int, message: str, service_id: str = "") -> RedirectResponse:
    query = f"message={quote(message)}"
    if service_id:
        query += f"&service_id={quote(service_id)}"
    return RedirectResponse(
        f"/customers/{customer_id}/plume?{query}", status_code=303
    )


def _plume_targets(customer: Customer, network: PlumeCustomerNetwork | None, service_id: str) -> tuple[str, str]:
    customer_id = str(network.plume_customer_id or "").strip() if network else ""
    location_id = str(network.plume_location_id or "").strip() if network else ""
    if customer_id and location_id:
        return customer_id, location_id
    snapshot = _resolved_plume_snapshot(customer, network, service_id)
    return str(snapshot["customer_id"]), str(snapshot["location_id"])


def _resolved_plume_snapshot(
    customer: Customer,
    network: PlumeCustomerNetwork | None,
    service_id: str,
) -> dict:
    """Resolve an existing Plume account using every exact account identity.

    Older imports commonly use the Platypus customer ID as Plume accountId,
    while NOP-created accounts use the NOP customer number. A node inventory
    lookup may omit locationId, so account lookup must be allowed to supply it.
    """
    location_id = str(network.plume_location_id or "").strip() if network else ""
    hints = [
        _plume_customer_hint(customer, network),
        str(customer.customer_number or "").strip(),
    ]
    unique_hints = list(dict.fromkeys(hint for hint in hints if hint)) or [""]
    errors: list[str] = []
    for hint in unique_hints:
        try:
            return PlumeReadService().snapshot(
                service_id=service_id,
                customer_id=hint,
                location_id=location_id,
            )
        except (PlumeError, ValueError) as exc:
            errors.append(f"{hint or 'no account hint'}: {exc}")
    # Imported/migrated accounts frequently have a Plume accountId that does
    # not match either NOP or Platypus. Resolve the exact email through Plume's
    # V2 multi-entity search, but only accept one unambiguous native location.
    emails = [str(getattr(customer, "billing_email", "") or "").strip()]
    try:
        emails.append(str(customer.primary_contact.email or "").strip() if customer.primary_contact else "")
    except Exception:
        pass
    service = PlumeReadService()
    for email in dict.fromkeys(item for item in emails if item):
        try:
            identity = service.resolve_customer_identity(email, "email")
            if identity:
                return service.snapshot(
                    customer_id=identity["customer_id"],
                    location_id=identity["location_id"],
                )
        except (PlumeError, ValueError) as exc:
            errors.append(f"email {email}: {exc}")
    raise ValueError("; ".join(errors))


def _normalized_identifier(value: object) -> str:
    return "".join(ch for ch in str(value or "") if ch.isalnum()).upper()


def _platypus_service_identifiers(service: dict) -> set[str]:
    values = {service.get("s_data")}
    detail = service.get("detail") or {}
    if isinstance(detail, dict):
        for key, value in detail.items():
            key_text = "".join(ch for ch in str(key).lower() if ch.isalnum())
            if any(token in key_text for token in ("serial", "pod", "plume", "gateway", "location")):
                values.add(value)
    return {item for value in values if (item := _normalized_identifier(value))}


def _billing_role_for_rate(name: object) -> str:
    lowered = str(name or "").strip().lower()
    if any(token in lowered for token in ("extender", "additional pod", "additional plume")):
        return "extender"
    if "gateway" in lowered and any(token in lowered for token in ("plume", "wifi", "wi-fi")):
        return "gateway"
    return ""


def _available_billing_rates(rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    # The web-rate API may return one row per billing frequency. Prefer the
    # monthly row, then expose each RGID only once in the staff dropdown.
    ordered = sorted(rows, key=lambda row: str(row.get("r_frequency") or "1") != "1")
    for row in ordered:
        rate_id = str(row.get("id") or row.get("ID") or row.get("rgid") or row.get("rg_id") or "").strip()
        name = str(row.get("name") or row.get("Name") or row.get("rg_name") or "").strip()
        role = _billing_role_for_rate(name)
        if rate_id and role and rate_id not in seen:
            result.append({
                "id": rate_id,
                "name": name,
                "role": role,
                "frequency": str(row.get("r_frequency") or "1"),
                "price": str(row.get("rg_fixed_price") or ""),
            })
            seen.add(rate_id)
    return result


async def _billing_rate_options(
    client: PlatypusClient,
    customer_id: str,
    store_id: str = "",
) -> list[dict]:
    try:
        if not store_id:
            customer = await client.get_customer(customer_id)
            store_id = str(customer.get("storeid") or customer.get("store_id") or "").strip()
        if not store_id:
            raise ValueError("Platypus did not return a store ID for this customer.")
        options = _available_billing_rates(
            await client.get_available_web_rates(customer_id, store_id)
        )
    except PlatypusError as exc:
        if getattr(exc, "code", "") != "DATA_ERROR":
            raise
        options = []
    if not any(item["id"] == PLATYPUS_POD_EXTENDER_RATE["id"] for item in options):
        options.append(dict(PLATYPUS_POD_EXTENDER_RATE))
    return options


def _service_tree_type(
    rows: list[dict],
    *,
    crid: str,
    role: str,
    hardware_kind: str = "pod",
) -> str:
    candidates = [row for row in rows if str(row.get("rs_cr_id") or "").strip() == str(crid)]
    # Gateway RGID 297 contains both a regular Plume POD definition and an
    # integrated Adtran Gateway definition. Billing role alone is insufficient.
    if role == "extender" or hardware_kind != "adtran_gateway":
        preferred = [
            row for row in candidates
            if "plume" in str(row.get("rs_path") or "").lower()
            and "pod" in str(row.get("rs_path") or "").lower()
        ]
    else:
        preferred = [
            row for row in candidates
            if "adtran" in str(row.get("rs_path") or "").lower()
            and "gateway" in str(row.get("rs_path") or "").lower()
        ]
    selected = preferred or candidates
    service_ids = list(dict.fromkeys(str(row.get("rs_svc_id") or "").strip() for row in selected if row.get("rs_svc_id")))
    if len(service_ids) != 1:
        paths = ", ".join(str(row.get("rs_path") or row.get("rs_svc_id") or "unknown") for row in selected)
        raise ValueError(f"Unable to identify one {role} service definition on the new rate. Service tree: {paths or 'empty'}")
    return service_ids[0]


def _plume_hardware_kind(snapshot: dict, serial_number: str) -> str:
    """Classify the claimed node for Platypus service-definition selection."""
    wanted = _normalized_identifier(serial_number)
    for pod in snapshot.get("pods") or []:
        aliases = {
            _normalized_identifier(pod.get(key))
            for key in ("serial_number", "id", "mac_address")
        }
        if wanted not in aliases:
            continue
        raw = pod.get("raw") if isinstance(pod.get("raw"), dict) else {}
        model_text = " ".join(
            str(value or "")
            for value in (
                pod.get("model"), raw.get("model"), raw.get("modelName"),
                raw.get("deviceModel"), raw.get("manufacturer"), raw.get("vendor"),
            )
        ).lower()
        if "adtran" in model_text or "854-v" in model_text or "854v" in model_text:
            return "adtran_gateway"
        return "pod"
    return "pod"


def _service_fields(rows: list[dict], serial_number: str, account_id: str) -> list[dict[str, str]]:
    writable = [row for row in rows if str(row.get("readonly") or "N").upper() != "Y" and row.get("datacol")]
    pod_fields = [row for row in writable if any(token in f"{row.get('datacol','')} {row.get('datahdr','')}".lower().replace(" ", "") for token in ("podid", "serial", "gatewayid", "plumeid", "deviceid"))]
    account_fields = [row for row in writable if "accountid" in f"{row.get('datacol','')} {row.get('datahdr','')}".lower().replace(" ", "")]
    preferred = pod_fields or [row for row in writable if any(token in f"{row.get('datacol','')} {row.get('datahdr','')}".lower() for token in ("serial", "pod", "gateway", "plume", "device"))]
    searchable = [row for row in writable if str(row.get("search") or "").upper() == "Y"]
    target = (preferred or searchable or writable or [None])[0]
    if target is None:
        raise ValueError("Platypus returned no writable custom field for the pod serial.")
    fields: list[dict[str, str]] = []
    missing_required: list[str] = []
    for row in writable:
        column = str(row.get("datacol") or "").strip()
        if row in pod_fields or (not pod_fields and row is target):
            value = serial_number.strip()
        elif row in account_fields:
            value = account_id.strip()
        else:
            value = str(row.get("template_dflt") or row.get("dflt") or "").strip()
        if value.upper() == "NULL":
            value = ""
        if str(row.get("reqd") or "N").upper() == "Y" and not value:
            missing_required.append(str(row.get("datahdr") or column))
        if value or row is target:
            fields.append({"column_name": column, "newvalue": value, "oldvalue": "", "control": str(row.get("ctrl") or "txt_text"), "display": str(row.get("datahdr") or column)})
    if missing_required:
        raise ValueError("Required Platypus service fields have no template default: " + ", ".join(missing_required))
    return fields


def _billing_cross_check(profile: dict, snapshot: dict | None, rate_options: list[dict]) -> dict:
    billed_identifiers: set[str] = set()
    gateway_billed = False
    extender_billed = False
    assignments: list[dict] = []
    for rate in profile.get("rates") or []:
        if not isinstance(rate, dict):
            continue
        rgid = str(rate.get("rgid") or rate.get("rg_id") or "").strip()
        rate_name = str(rate.get("rg_name") or rate.get("name") or "").strip()
        role = _billing_role_for_rate(rate_name)
        is_gateway = role == "gateway"
        is_extender = role == "extender"
        gateway_billed = gateway_billed or is_gateway
        extender_billed = extender_billed or is_extender
        for service in rate.get("services") or []:
            if isinstance(service, dict):
                billed_identifiers.update(_platypus_service_identifiers(service))
        if is_gateway or is_extender:
            assignments.append({"crid": str(rate.get("crid") or rate.get("cr_id") or ""), "rgid": rgid, "name": rate_name, "role": "gateway" if is_gateway else "extender"})
    if snapshot:
        for pod in snapshot.get("pods") or []:
            aliases = {_normalized_identifier(pod.get(key)) for key in ("serial_number", "id", "mac_address")}
            aliases.discard("")
            pod["platypus_billed"] = bool(aliases & billed_identifiers)
            pod["billing_suggestion"] = "extender" if gateway_billed else "gateway"
    configured = {role: any(item["role"] == role for item in rate_options) for role in ("gateway", "extender")}
    return {"gateway_billed": gateway_billed, "extender_billed": extender_billed, "assignments": assignments, "configured": configured}


def _require_speed_test_access(request: Request) -> None:
    context = context_from_request(request)
    if not (context.is_staff or context.is_support_partner):
        raise HTTPException(
            status_code=403,
            detail="Pod speed tests are available only to NTInet staff and third-party support.",
        )


def _require_wifi_email_access(request: Request) -> None:
    context = context_from_request(request)
    if not (context.is_staff or context.is_support_partner):
        raise HTTPException(
            status_code=403,
            detail="Wi-Fi details may be emailed only by NTInet staff and third-party support.",
        )


def _require_plume_management_access(request: Request) -> None:
    if not context_from_request(request).is_staff:
        raise HTTPException(
            status_code=403,
            detail="Plume onboarding and pod management are restricted to NTInet staff.",
        )


@router.get("/{customer_id}/plume", response_class=HTMLResponse)
def plume_customer_detail(
    request: Request,
    customer_id: int,
    service_id: str = "",
    message: str = "",
    error: str = "",
):
    require_permission(request, "customers.read")
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(
            select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id)
        )
        _ = tuple(customer.locations)
        _ = tuple(customer.services)
        if network:
            _ = network.location
            _ = tuple(network.pods)
            _ = tuple(network.devices)
        platypus_id = customer.platypus_link.external_id if customer.platypus_link else ""
        plume_customer_hint = _plume_customer_hint(customer, network)
        db.expunge_all()
    live_snapshot = None
    live_error = error
    try:
        live_snapshot = PlumeReadService().snapshot(
            service_id=service_id,
            customer_id=plume_customer_hint,
            location_id=(network.plume_location_id if network else ""),
        )
    except (PlumeError, ValueError) as exc:
        live_error = str(exc)
    return render(
        request,
        "customers/plume.html",
        customer=customer,
        network=network,
        live_snapshot=live_snapshot,
        service_id=service_id,
        return_url=(f"/customers/{platypus_id}" if platypus_id else f"/customers/local/{customer.id}"),
        plume_configured=plume_client.configured,
        message=message,
        error=live_error,
        can_run_speed_test=(
            context_from_request(request).is_staff
            or context_from_request(request).is_support_partner
        ),
        can_email_wifi=(
            context_from_request(request).is_staff
            or context_from_request(request).is_support_partner
        ),
        can_manage_plume=context_from_request(request).is_staff,
    )


@router.get("/{customer_id}/plume/manage", response_class=HTMLResponse)
async def plume_manage(request: Request, customer_id: int, service_id: str = "", message: str = "", error: str = "", pending_serial: str = ""):
    require_permission(request, "customers.read")
    _require_plume_management_access(request)
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id))
        plume_customer_hint = _plume_customer_hint(customer, network)
        primary_contact = customer.primary_contact
        primary_location = customer.primary_location
        defaults = {
            "account_id": customer.customer_number,
            "name": customer.name,
            "email": (primary_contact.email if primary_contact else "") or customer.billing_email,
            "location_name": primary_location.name if primary_location else "Primary Location",
        }
        platypus_id = str(customer.platypus_link.external_id or "").strip() if customer.platypus_link else ""
        db.expunge_all()
    snapshot = None
    live_error = error
    try:
        snapshot = _resolved_plume_snapshot(customer, network, service_id)
    except (PlumeError, ValueError) as exc:
        if not live_error:
            live_error = str(exc)
    billing = {"gateway_billed": False, "extender_billed": False, "assignments": [], "configured": {"gateway": True, "extender": True}}
    billing_error = ""
    if platypus_id and snapshot:
        try:
            billing_profile = await CustomerDirectory(PlatypusClient()).get(platypus_id)
            billing = _billing_cross_check(
                billing_profile,
                snapshot,
                [
                    {"id": "297", "name": "Plume Smart Wifi Gateway", "role": "gateway"},
                    dict(PLATYPUS_POD_EXTENDER_RATE),
                ],
            )
        except PlatypusError as exc:
            billing_error = str(exc)
    return render(
        request,
        "customers/plume_manage.html",
        customer=customer,
        network=network,
        snapshot=snapshot,
        defaults=defaults,
        service_id=service_id,
        message=message,
        error=live_error,
        billing=billing,
        billing_error=billing_error,
        pending_serial=pending_serial,
        platypus_id=platypus_id,
    )


@router.post("/{customer_id}/plume/onboard")
def plume_onboard(
    request: Request,
    customer_id: int,
    account_id: str = Form(""),
    customer_name: str = Form(""),
    email: str = Form(""),
    location_name: str = Form("Primary Location"),
    serial_number: str = Form(""),
    pod_name: str = Form(""),
):
    require_permission(request, "customers.read")
    _require_plume_management_access(request)
    context = context_from_request(request)
    service = PlumeProvisioningService()
    stage = "inventory lookup"
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        try:
            inventory = service.node_inventory(serial_number)
            stage = "customer registration"
            created_customer = service.register_customer(
                account_id=account_id,
                name=customer_name or customer.name,
                email=email,
                partner_id=str(inventory.get("partnerId") or ""),
            )
            plume_customer_id = created_customer["id"]
            stage = "location creation"
            created_location = service.create_location(
                customer_id=plume_customer_id, name=location_name
            )
            plume_location_id = created_location["id"]
            stage = "pod claim"
            service.claim_node(
                customer_id=plume_customer_id,
                location_id=plume_location_id,
                serial_number=serial_number,
                nickname=pod_name,
            )
        except (PlumeError, ValueError) as exc:
            return RedirectResponse(
                f"/customers/{customer_id}/plume/manage?error={quote(f'Onboarding stopped during {stage}: {exc}')}",
                status_code=303,
            )
        network = db.scalar(select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id))
        if network is None:
            network = PlumeCustomerNetwork(customer_id=customer.id)
            db.add(network)
        network.plume_customer_id = plume_customer_id
        network.plume_location_id = plume_location_id
        network.network_name = location_name.strip()
        network.service_status = "active"
        network.sync_status = "not_synced"
        AuditService(db, request, context).record(
            "plume.customer_onboarded", "customer", customer.id,
            f"Onboarded Plume account {account_id} and claimed node {serial_number}.",
            module="customer-management", organization_id=customer.owner_organization_id,
            event_data={"plume_customer_id": plume_customer_id, "plume_location_id": plume_location_id, "node_serial": serial_number},
        )
        db.commit()
    return RedirectResponse(f"/customers/{customer_id}/plume/manage?message={quote('Plume customer onboarded and pod claimed.')}", status_code=303)


@router.post("/{customer_id}/plume/pods/add")
def plume_add_pod(request: Request, customer_id: int, serial_number: str = Form(""), pod_name: str = Form(""), service_id: str = Form("")):
    require_permission(request, "customers.read")
    _require_plume_management_access(request)
    context = context_from_request(request)
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id))
        try:
            plume_customer_id, plume_location_id = _plume_targets(customer, network, service_id)
            PlumeProvisioningService().claim_node(customer_id=plume_customer_id, location_id=plume_location_id, serial_number=serial_number, nickname=pod_name)
            if network is None:
                network = PlumeCustomerNetwork(customer_id=customer.id)
                db.add(network)
            network.plume_customer_id = plume_customer_id
            network.plume_location_id = plume_location_id
            network.service_status = "active"
            network.sync_status = "not_synced"
            network.last_sync_error = ""
        except (PlumeError, ValueError) as exc:
            return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&error={quote(f'Unable to add pod: {exc}')}", status_code=303)
        AuditService(db, request, context).record("plume.pod_claimed", "customer", customer.id, f"Claimed Plume pod {serial_number} ({pod_name or 'unnamed'}).", module="customer-management", organization_id=customer.owner_organization_id, event_data={"serial_number": serial_number, "nickname": pod_name, "plume_customer_id": plume_customer_id, "plume_location_id": plume_location_id})
        db.commit()
    # Replay the staff-confirmed form to the billing step. Manage Plume does not
    # expose general rate selection; adding an additional pod always uses the
    # configured Plume extender rate (RGID 298) and creates its service values.
    return RedirectResponse(f"/customers/{customer_id}/plume/billing/add", status_code=307)


@router.post("/{customer_id}/plume/billing/add")
async def plume_add_billing(
    request: Request,
    customer_id: int,
    serial_number: str = Form(""),
    rate_selection: str = Form(""),
    confirmation: str = Form(""),
    service_id: str = Form(""),
):
    require_permission(request, "customers.read")
    _require_plume_management_access(request)
    try:
        parts = rate_selection.split(":")
        if len(parts) == 3:
            selected_rgid, _frequency, billing_action = parts
        else:
            billing_action, selected_rgid = parts
    except ValueError:
        raise HTTPException(400, "Choose a Platypus billing rate.")
    if billing_action not in {"gateway", "extender"} or not selected_rgid.strip():
        raise HTTPException(400, "Choose a valid Gateway or Extender rate.")
    if confirmation.strip().upper() not in {"ADD BILLING", "ADD RATE"}:
        raise HTTPException(400, "Confirm the Platypus rate and service addition.")
    rgid = selected_rgid.strip()
    context = context_from_request(request)
    client = PlatypusClient()
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        platypus_id = str(customer.platypus_link.external_id or "").strip() if customer.platypus_link else ""
        if not platypus_id:
            raise HTTPException(400, "This NOP customer is not linked to Platypus.")
        try:
            profile = await CustomerDirectory(client).get(platypus_id)
            existing = {
                identifier
                for rate in profile.get("rates") or [] if isinstance(rate, dict)
                for service in rate.get("services") or [] if isinstance(service, dict)
                for identifier in _platypus_service_identifiers(service)
            }
            if _normalized_identifier(serial_number) in existing:
                raise ValueError("This pod serial already has a Platypus service and will not be billed twice.")
            available = await _billing_rate_options(
                client,
                platypus_id,
                str((profile.get("customer") or {}).get("storeid") or ""),
            )
            chosen = next((item for item in available if item["id"] == rgid and item["role"] == billing_action), None)
            if chosen is None:
                raise ValueError("The selected Platypus rate is no longer available for this billing role.")
            incomplete_crids = [
                str(rate.get("crid") or rate.get("cr_id") or "").strip()
                for rate in profile.get("rates") or [] if isinstance(rate, dict)
                if str(rate.get("rgid") or rate.get("rg_id") or "").strip() == rgid
                and not (rate.get("services") or [])
                and str(rate.get("crid") or rate.get("cr_id") or "").strip()
            ]
            if len(incomplete_crids) > 1:
                raise ValueError(
                    "Multiple incomplete Platypus rates exist for this RGID (CRIDs "
                    + ", ".join(incomplete_crids)
                    + "). Repair them in Platypus before retrying."
                )
            reused_rate = bool(incomplete_crids)
            crid = incomplete_crids[0] if reused_rate else await client.add_rate(platypus_id, rgid, frequency=1, quantity=1)
            try:
                network = db.scalar(select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id))
                plume_snapshot = _resolved_plume_snapshot(customer, network, service_id)
                hardware_kind = _plume_hardware_kind(plume_snapshot, serial_number)
                plat_service_id = _service_tree_type(
                    await client.list_service_tree(platypus_id),
                    crid=crid,
                    role=billing_action,
                    hardware_kind=hardware_kind,
                )
                plume_account_id = str(plume_snapshot.get("account_id") or customer.customer_number or "").strip()
                if not plume_account_id:
                    raise ValueError("Plume did not return an account ID for the required Platypus service field.")
                custom_fields = _service_fields(
                    await client.get_service_info(plat_service_id, rgid=rgid, crid=crid),
                    serial_number,
                    plume_account_id,
                )
                data_id = await client.add_service(
                    platypus_id,
                    service_type_id=plat_service_id,
                    crid=crid,
                    custom_fields=custom_fields,
                )
            except (PlatypusError, ValueError) as exc:
                rate_verb = "Reused incomplete" if reused_rate else "Added"
                AuditService(db, request, context).record("platypus.plume_billing_partial", "customer", customer.id, f"{rate_verb} Platypus {billing_action} rate CRID {crid}, but its pod service failed: {exc}", module="customer-management", organization_id=customer.owner_organization_id, event_data={"crid": crid, "rgid": rgid, "serial_number": serial_number, "billing_action": billing_action, "reused_rate": reused_rate})
                db.commit()
                return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&pending_serial={quote(serial_number)}&error={quote(f'Rate CRID {crid} exists, but the pod service failed. NOP will reuse this CRID on the next retry. Error: {exc}')}", status_code=303)
            refreshed = await CustomerDirectory(client).get(platypus_id)
            PlatypusCustomerSync(db, context).sync(refreshed)
        except (PlatypusError, ValueError) as exc:
            return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&pending_serial={quote(serial_number)}&error={quote(f'Unable to add Platypus billing: {exc}')}", status_code=303)
        action_text = "Repaired" if reused_rate else "Added"
        AuditService(db, request, context).record("platypus.plume_billing_added", "customer", customer.id, f"{action_text} Platypus {billing_action} billing for pod {serial_number} (CRID {crid}, Data ID {data_id}).", module="customer-management", organization_id=customer.owner_organization_id, event_data={"crid": crid, "rgid": rgid, "service_type_id": plat_service_id, "data_id": data_id, "serial_number": serial_number, "billing_action": billing_action, "hardware_kind": hardware_kind, "reused_rate": reused_rate, "plume_account_id": plume_account_id})
        db.commit()
    result_verb = "repaired" if reused_rate else "added"
    return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&message={quote(f'Platypus {billing_action} billing {result_verb} and NOP synchronized.')}", status_code=303)


@router.post("/{customer_id}/plume/pods/{node_id}/rename")
def plume_rename_pod(request: Request, customer_id: int, node_id: str, nickname: str = Form(""), service_id: str = Form("")):
    require_permission(request, "customers.read")
    _require_plume_management_access(request)
    context = context_from_request(request)
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id))
        try:
            plume_customer_id, plume_location_id = _plume_targets(customer, network, service_id)
            PlumeProvisioningService().rename_node(customer_id=plume_customer_id, location_id=plume_location_id, node_id=node_id, nickname=nickname)
        except (PlumeError, ValueError) as exc:
            return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&error={quote(f'Unable to rename pod: {exc}')}", status_code=303)
        AuditService(db, request, context).record("plume.pod_renamed", "customer", customer.id, f"Renamed Plume pod {node_id} to {nickname}.", module="customer-management", organization_id=customer.owner_organization_id, event_data={"node_id": node_id, "nickname": nickname})
        db.commit()
    return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&message={quote('Pod name updated.')}", status_code=303)


@router.post("/{customer_id}/plume/pods/{node_id}/remove")
async def plume_remove_pod(request: Request, customer_id: int, node_id: str, confirmation: str = Form(""), service_id: str = Form("")):
    require_permission(request, "customers.read")
    _require_plume_management_access(request)
    if confirmation.strip().upper() != "UNCLAIM":
        raise HTTPException(400, "Type UNCLAIM to confirm pod removal.")
    context = context_from_request(request)
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id))
        platypus_id = str(customer.platypus_link.external_id or "").strip() if customer.platypus_link else ""
        matched_rate: dict | None = None
        matched_crid = ""
        profile: dict = {}
        try:
            plume_customer_id, plume_location_id = _plume_targets(customer, network, service_id)
            if platypus_id:
                profile = await CustomerDirectory(PlatypusClient()).get(platypus_id)
                wanted = _normalized_identifier(node_id)
                matching_rates = [
                    rate for rate in (profile.get("rates") or []) if isinstance(rate, dict)
                    and any(
                        wanted in _platypus_service_identifiers(service)
                        for service in (rate.get("services") or []) if isinstance(service, dict)
                    )
                ]
                if len(matching_rates) > 1:
                    crids = ", ".join(
                        str(rate.get("crid") or rate.get("cr_id") or "")
                        for rate in matching_rates
                    )
                    raise ValueError(
                        f"This pod matches multiple Platypus rates (CRIDs {crids}). Nothing was removed."
                    )
                if matching_rates:
                    matched_rate = matching_rates[0]
                    matched_crid = str(matched_rate.get("crid") or matched_rate.get("cr_id") or "").strip()
                    if not matched_crid:
                        raise ValueError("The matching Platypus rate did not include a CRID. Nothing was removed.")
            PlumeProvisioningService().unclaim_node(customer_id=plume_customer_id, location_id=plume_location_id, node_id=node_id)
            if matched_crid:
                try:
                    billing_client = PlatypusClient()
                    await billing_client.delete_rate(platypus_id, matched_crid, no_closeout=False)
                    refreshed = await CustomerDirectory(billing_client).get(platypus_id)
                    PlatypusCustomerSync(db, context).sync(refreshed)
                except PlatypusError as exc:
                    raise ValueError(
                        f"The pod was unclaimed from Plume, but Platypus CRID {matched_crid} could not be deleted. Retry from Manage Rates. Error: {exc}"
                    ) from exc
        except (PlumeError, PlatypusError, ValueError) as exc:
            return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&error={quote(f'Unable to remove pod: {exc}')}", status_code=303)
        result_text = f"Unclaimed Plume pod {node_id}; preserved package and inventory identity."
        if matched_crid:
            result_text += f" Deleted matching Platypus rate and service CRID {matched_crid}."
        else:
            result_text += " No matching Platypus rate/service existed."
        AuditService(db, request, context).record("plume.pod_unclaimed", "customer", customer.id, result_text, module="customer-management", organization_id=customer.owner_organization_id, event_data={"node_id": node_id, "preserve_pack_id": True, "remove_account_id": False, "platypus_crid_deleted": matched_crid})
        db.commit()
    message = "Pod removed from Plume and retained in inventory."
    if matched_crid:
        message += f" Platypus rate and service CRID {matched_crid} were also deleted."
    else:
        message += " No matching Platypus billing record existed."
    return RedirectResponse(f"/customers/{customer_id}/plume/manage?service_id={quote(service_id)}&message={quote(message)}", status_code=303)


@router.post("/{customer_id}/plume/email-wifi-details")
def plume_email_wifi_details(
    request: Request,
    customer_id: int,
    service_id: str = Form(""),
):
    require_permission(request, "customers.read")
    _require_wifi_email_access(request)
    context = context_from_request(request)
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(
            select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id)
        )
        plume_customer_hint = _plume_customer_hint(customer, network)
        try:
            service = PlumeReadService()
            snapshot = service.snapshot(
                service_id=service_id,
                customer_id=plume_customer_hint,
                location_id=(network.plume_location_id if network else ""),
            )
            recipient = str(snapshot.get("customer_email") or "").strip()
            if not recipient or "@" not in recipient:
                raise ValueError("Plume does not have a valid customer email address on record.")
            credentials = service.network_credentials(
                customer_id=snapshot["customer_id"],
                location_id=snapshot["location_id"],
            )
            body = render_email_template(
                "plume_wifi_details.txt",
                customer_name=snapshot.get("customer_name") or customer.name,
                ssid=credentials["ssid"],
                wifi_password=credentials["password"],
            )
            result = send_email(
                "Your Wi-Fi network details",
                body,
                [recipient],
            )
            if not result.ok:
                raise ValueError(result.message)
        except (PlumeError, ValueError, OSError) as exc:
            return _redirect(customer.id, f"Unable to email Wi-Fi details: {exc}", service_id)

        AuditService(db, request, context).record(
            "plume.wifi_details_emailed",
            "customer",
            customer.id,
            f"Emailed Wi-Fi details to the Plume email on record ({recipient}).",
            module="customer-management",
            organization_id=customer.owner_organization_id,
            event_data={
                "recipient": recipient,
                "plume_customer_id": snapshot["customer_id"],
                "plume_location_id": snapshot["location_id"],
            },
        )
        db.commit()
    return _redirect(customer_id, f"Wi-Fi details emailed to {recipient}.", service_id)


@router.post("/{customer_id}/plume/pods/{node_id}/speed-test")
def plume_run_speed_test(
    request: Request,
    customer_id: int,
    node_id: str,
    service_id: str = Form(""),
):
    require_permission(request, "customers.read")
    _require_speed_test_access(request)
    context = context_from_request(request)
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(
            select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id)
        )
        plume_customer_hint = _plume_customer_hint(customer, network)
        snapshot = PlumeReadService().snapshot(
            service_id=service_id,
            customer_id=plume_customer_hint,
            location_id=(network.plume_location_id if network else ""),
        )
        pod = next((item for item in snapshot["pods"] if item["id"] == node_id), None)
        if pod is None:
            raise HTTPException(status_code=404, detail="Plume pod not found at this customer location")
        try:
            result = PlumeReadService().run_speed_test(
                customer_id=snapshot["customer_id"],
                location_id=snapshot["location_id"],
                node_id=node_id,
            )
        except (PlumeError, ValueError) as exc:
            return _redirect(customer.id, f"Unable to start speed test: {exc}", service_id)
        request_id = str(
            result.get("requestId") or result.get("id") or result.get("speedTestId") or ""
        ).strip()
        detail = f" Request ID: {request_id}." if request_id else ""
        AuditService(db, request, context).record(
            "plume.speed_test_started",
            "customer",
            customer.id,
            f"Started Plume speed test for pod {pod['name']}.{detail}",
            module="customer-management",
            organization_id=customer.owner_organization_id,
            event_data={
                "plume_customer_id": snapshot["customer_id"],
                "plume_location_id": snapshot["location_id"],
                "node_id": node_id,
                "request_id": request_id,
            },
        )
        db.commit()
    return _redirect(
        customer_id,
        f"Speed test started for {pod['name']}.{detail} Refresh shortly to view the result.",
        service_id,
    )


@router.get("/{customer_id}/plume/devices/{mac_address}", response_class=HTMLResponse)
def plume_device_detail(
    request: Request,
    customer_id: int,
    mac_address: str,
    service_id: str = "",
):
    require_permission(request, "customers.read")
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        network = db.scalar(
            select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id)
        )
        platypus_id = customer.platypus_link.external_id if customer.platypus_link else ""
        plume_customer_hint = _plume_customer_hint(customer, network)
        db.expunge_all()
    error = ""
    diagnostics_error = ""
    device = None
    try:
        service = PlumeReadService()
        snapshot = service.snapshot(
            service_id=service_id,
            customer_id=plume_customer_hint,
            location_id=(network.plume_location_id if network else ""),
        )
        pod_names = {
            "".join(ch for ch in str(alias) if ch.isalnum()).lower(): pod["name"]
            for pod in snapshot["pods"] for alias in pod["aliases"] if alias
        }
        normalized_mac = "".join(ch for ch in mac_address if ch.isalnum()).upper()
        list_device = next((
            item for item in snapshot["devices"]
            if "".join(ch for ch in item["mac_address"] if ch.isalnum()).upper()
            == normalized_mac
        ), None)
        list_raw = list_device.get("raw", {}) if list_device else {}
        network_id = str(
            list_raw.get("networkId")
            or (list_raw.get("network") or {}).get("id", "")
            if isinstance(list_raw, dict) else ""
        ).strip()
        try:
            device = service.device_detail(
                customer_id=snapshot["customer_id"],
                location_id=snapshot["location_id"],
                mac_address=mac_address,
                pod_names=pod_names,
                network_id=network_id,
            )
            if list_device is not None:
                if device.get("signal_strength") is None:
                    device["signal_strength"] = list_device.get("signal_strength")
                list_metadata = service.device_metadata(list_device.get("raw", {}))
                for key, value in list_metadata.items():
                    if device.get(key) in (None, "", [], {}):
                        device[key] = value
        except PlumeError:
            if list_device is None:
                raise
            device = dict(list_device)
            for key, value in service.device_metadata(list_device.get("raw", {})).items():
                if value not in (None, "", [], {}):
                    device[key] = value
        try:
            extras = service.device_extras(
                customer_id=snapshot["customer_id"],
                location_id=snapshot["location_id"],
                mac_address=mac_address,
            )
            for key, value in extras.items():
                if value not in (None, "", [], {}) or key in {
                    "rssi_history", "rssi_min", "rssi_max", "signal_strength"
                }:
                    device[key] = value
        except Exception as exc:
            diagnostics_error = f"Optional Plume diagnostics could not be normalized: {exc}"
    except Exception as exc:
        error = str(exc)
    if device is not None:
        defaults = {
            "ssid": "", "channel": "", "model": "", "manufacturer": "",
            "operating_system": "", "operating_system_version": "",
            "category": "", "classification_id": "", "capabilities": "",
            "wifi_standard": "", "security": "", "interference": None,
            "alarms": "", "health": "", "opensync_steering": None,
            "cloud_steering": None, "coverage_alarm": "",
            "out_of_home_protection": "", "mac_stitching": "",
            "bandwidth_download": None, "bandwidth_upload": None,
            "signal_strength": None, "signal_health": "unknown",
            "rssi_min": None, "rssi_max": None, "rssi_history": [],
            "qoe_score": None, "latency": None, "jitter": None,
            "packet_loss": None, "stitch_history_count": 0,
            "stitch_last_seen": "",
            "predicted_wifi_speed": None, "minimum_wifi_speed": None,
            "channel_utilization": None, "first_connected": "",
            "connection_state_changed": "",
        }
        for key, value in defaults.items():
            device.setdefault(key, value)
    return render(
        request,
        "customers/plume_device.html",
        customer=customer,
        device=device,
        error=error,
        diagnostics_error=diagnostics_error,
        service_id=service_id,
        return_url=(
            f"/customers/{customer.id}/plume?service_id={quote(service_id)}"
            if service_id else f"/customers/{customer.id}/plume"
        ),
        customer_return_url=(
            f"/customers/{platypus_id}" if platypus_id else f"/customers/local/{customer.id}"
        ),
    )


@router.post("/{customer_id}/plume/test")
def plume_connection_test(request: Request, customer_id: int):
    require_permission(request, "customers.manage")
    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        try:
            status = plume_client.connection_status()
        except PlumeError as exc:
            return _redirect(customer.id, f"Plume connection failed: {exc}")
    return _redirect(
        customer_id,
        f"Plume authentication successful. Token expires in approximately {status['expires_in']} seconds.",
    )


@router.post("/{customer_id}/plume/link")
def plume_link_customer(
    request: Request,
    customer_id: int,
    plume_customer_id: str = Form(""),
    plume_location_id: str = Form(""),
    customer_location_id: str = Form(""),
    network_name: str = Form(""),
    service_status: str = Form("pending"),
):
    require_permission(request, "customers.manage")
    context = context_from_request(request)
    allowed_statuses = {"pending", "active", "suspended", "disconnected"}
    if service_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid Plume service status")
    if not plume_customer_id.strip() and not plume_location_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Enter a Plume customer ID or location ID.",
        )

    with SessionLocal() as db:
        customer = _customer_or_404(db, request, customer_id)
        location_id = int(customer_location_id) if customer_location_id.strip() else None
        if location_id and location_id not in {location.id for location in customer.locations}:
            raise HTTPException(status_code=400, detail="Invalid customer location")
        network = db.scalar(
            select(PlumeCustomerNetwork).where(PlumeCustomerNetwork.customer_id == customer.id)
        )
        if network is None:
            network = PlumeCustomerNetwork(customer_id=customer.id)
            db.add(network)
        network.customer_location_id = location_id
        network.plume_customer_id = plume_customer_id.strip()
        network.plume_location_id = plume_location_id.strip()
        network.network_name = network_name.strip()
        network.service_status = service_status
        network.sync_status = "not_synced"
        network.last_sync_error = ""
        db.flush()
        AuditService(db, request, context).record(
            "plume.customer_linked",
            "plume_customer_network",
            network.id,
            f"Updated Plume association for {customer.customer_number}",
            module="customer-management",
            organization_id=customer.owner_organization_id,
            event_data={
                "plume_customer_id": network.plume_customer_id,
                "plume_location_id": network.plume_location_id,
                "service_status": network.service_status,
            },
        )
        db.commit()
    return _redirect(customer_id, "Plume customer association saved.")
