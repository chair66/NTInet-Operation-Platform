from urllib.parse import quote_plus, urlparse
import json
import re
import secrets
import string
from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database.core import SessionLocal
from app.database.models import (
    DigiCloudDomain,
    DigiCloudOrganizationSettings,
    DigiCloudPhoneNumber,
    DigiCloudResellerDeviceModel,
)
from app.database.customer_models import Customer, CustomerService, ExternalRecordLink
from app.modules.access import user_can_access_module
from app.services.digicloud_user_access import (
    admin_organizations,
    allowed_user_domains,
    require_allowed_domain,
    require_user_management_access,
)
from sqlalchemy import or_, select, update
from app.security import context_from_request, require_permission, require_platform_staff
from app.services.digicloud_service import DigiCloudService
from app.services.digicloud_platypus_billing import (
    DIGICLOUD_RESIDENTIAL_RATES,
    DigiCloudBillingProvisionError,
    normalize_mac,
    provision_residential_billing,
)
from app.services.platypus import PlatypusClient, PlatypusAPIError
from app.services.customer_directory import CustomerDirectory
from app.services.platypus_customer_sync import PlatypusCustomerSync
from app.services.audit_service import AuditService
from app.providers.netsapiens import (
    NetSapiensClient,
    NetSapiensDevices,
    NetSapiensError,
    NetSapiensPhoneNumbers,
    NetSapiensPhoneProvisioning,
    NetSapiensUsers,
)
from app.providers.netsapiens.emergency_addresses import NetSapiensEmergencyAddresses
from app.providers.netsapiens.answering_rules import NetSapiensAnsweringRules
from app.web import render

router=APIRouter(prefix="/digicloud",tags=["digicloud"])
def redirect_error(path,exc): return RedirectResponse(f"{path}?error={quote_plus(str(exc.detail))}",303)
def bool_form(v): return str(v or "").lower() in {"1","true","on","yes"}


def _resolve_billing_target(
    org_settings,
    posted_customer_id: str,
    posted_rate_group_id: str,
) -> tuple[str, str, set[str]]:
    """Resolve billing server-side so wholesale clients cannot override the parent."""
    billing_model = str(org_settings.billing_model or "direct").strip().lower()
    customer_id = str(posted_customer_id or "").strip()
    rate_group_id = str(posted_rate_group_id or "").strip()
    allowed_wholesale_rates: set[str] = set()
    if billing_model == "wholesale":
        customer_id = str(org_settings.platypus_parent_customer_id or "").strip()
        try:
            parsed = json.loads(org_settings.wholesale_rate_group_ids or "[]")
            allowed_wholesale_rates = {
                str(value).strip() for value in parsed if str(value).strip()
            }
        except (TypeError, ValueError):
            allowed_wholesale_rates = set()
        if not customer_id or rate_group_id not in allowed_wholesale_rates:
            raise ValueError(
                "Wholesale billing account or rate is not configured for this reseller."
            )
    return customer_id, rate_group_id, allowed_wholesale_rates


def _did_digits(value) -> str:
    matches = re.findall(r"(?:1?\d{10})", str(value or ""))
    digits = re.sub(r"\D", "", matches[-1] if matches else str(value or ""))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else ""


def _domain_route_dids(rows: list[dict]) -> set[str]:
    """Return all 10-digit DIDs in the live domain, including inactive routes."""
    numbers: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = next((row.get(key) for key in (
            "phonenumber", "phone_number", "telephone_number", "number", "did", "matchrule"
        ) if row.get(key) not in (None, "")), "")
        digits = _did_digits(raw)
        if digits:
            numbers.add(digits)
    return numbers


def _eligible_domain_dids(
    db,
    local_domain: DigiCloudDomain | None,
    live_routes: list[dict],
    live_users: list[dict],
) -> tuple[list[str], dict[str, str]]:
    """Combine live and synced inventory, excluding existing user extensions."""
    candidates = _domain_route_dids(live_routes)
    statuses: dict[str, str] = {}
    if local_domain is not None:
        local_numbers = list(db.scalars(select(DigiCloudPhoneNumber).where(
            DigiCloudPhoneNumber.domain_id == local_domain.id,
            DigiCloudPhoneNumber.status != "deleted",
        )))
        for number in local_numbers:
            digits = _did_digits(number.telephone_number)
            if digits:
                candidates.add(digits)
                statuses[digits] = str(number.status or "available").replace("_", " ").title()

    occupied: set[str] = set()
    for row in live_users:
        if not isinstance(row, dict):
            continue
        for key in ("extension", "username", "user", "login"):
            digits = _did_digits(row.get(key))
            if digits:
                occupied.add(digits)
    eligible = sorted(candidates - occupied)
    return eligible, statuses


def _local_digicloud_domain(db, managed_domain) -> DigiCloudDomain | None:
    return db.scalar(select(DigiCloudDomain).where(
        DigiCloudDomain.domain_name == managed_domain.domain_name,
        DigiCloudDomain.deleted_at.is_(None),
    ))


def _ensure_local_digicloud_domain(db, managed_domain) -> DigiCloudDomain:
    """Materialize an already-authorized live reseller domain in NOP."""
    domain = db.scalar(select(DigiCloudDomain).where(
        DigiCloudDomain.domain_name == managed_domain.domain_name,
    ))
    if domain is None:
        domain = DigiCloudDomain(
            organization_id=managed_domain.organization_id,
            domain_name=managed_domain.domain_name,
            description=managed_domain.description or "",
            provider_domain_id=str(
                (managed_domain.raw or {}).get("id")
                or (managed_domain.raw or {}).get("domain_id")
                or managed_domain.domain_name
            ),
            status="active",
        )
        db.add(domain)
    else:
        domain.organization_id = managed_domain.organization_id
        domain.deleted_at = None
        domain.status = "active"
        if managed_domain.description:
            domain.description = managed_domain.description
    db.flush()
    return domain






def _phone_inventory_view(row: dict) -> dict:
    def first(*keys):
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return value
        return ""
    raw_mac = re.sub(r"[^0-9A-Fa-f]", "", str(first("mac", "device-provisioning-mac-address", "mac-address", "phone-mac"))).upper()
    mac = raw_mac if len(raw_mac) == 12 else ""
    subscriber = str(first("subscriber_name", "subscriber-name", "subscriber", "user", "device-provisioning-subscriber-name")).strip()

    # Some NetSapiens /phones responses omit subscriber_name even when the
    # hardware is assigned. Derive assigned extensions from the per-line
    # device fields so the inventory status and Assigned User column reflect
    # the live line assignments.
    assigned_extensions = []
    for index in range(1, 9):
        value = first(
            f"device{index}",
            f"device-{index}",
            f"device-provisioning-sip-uri-{index}",
            f"device-provisioning-sip-uri-{index}-value",
        )
        text = str(value or "").strip()
        if not text or text.casefold() in {"n/a", "available", "unassigned", "none"}:
            continue
        match = re.match(r"^sip:([^@;>]+)", text, flags=re.IGNORECASE)
        extension = (match.group(1) if match else text).strip()
        if extension and extension not in assigned_extensions:
            assigned_extensions.append(extension)

    if not subscriber and assigned_extensions:
        subscriber = ", ".join(assigned_extensions)

    domain = str(first("domain", "device-domain", "device-provisioning-domain")).strip()
    brand_model = str(first("brand_model", "device-models-brand-and-model", "device-models-model", "model", "device-provisioning-model")).strip()
    server = str(first("server", "preferred-server", "device-provisioning-registration-core-server", "core-server")).strip()
    transport = str(first("transport", "device-provisioning-sip-transport-protocol") or "udp").lower()
    notes = str(first("notes", "device-provisioning-notes")).strip()
    assigned = bool(subscriber)
    return {
        "mac": mac, "mac_display": ":".join(mac[i:i+2] for i in range(0, 12, 2)) if mac else "", "subscriber": subscriber,
        "domain": domain, "model": brand_model, "server": server,
        "transport": transport, "notes": notes, "assigned": assigned, "raw": row,
    }



def _find_phone_inventory(mac: str) -> dict:
    target = _normalize_mac(mac)
    for raw in NetSapiensPhoneProvisioning().list_phones():
        view = _phone_inventory_view(raw)
        if view["mac"] == target:
            return view
    return {}

def _hardware_scope(request: Request, db, organization_id: int | None = None):
    user = require_user_management_access(request)
    organizations = admin_organizations(db) if user.is_superuser else []
    if user.is_superuser:
        selected_org_id = organization_id or (organizations[0].id if organizations else None)
        all_domains = allowed_user_domains(db, user)
        domains = [item for item in all_domains if item.organization_id == selected_org_id] if selected_org_id is not None else []
    else:
        selected_org_id = user.organization_id
        domains = allowed_user_domains(db, user)
    return user, organizations, selected_org_id, domains

def _require_hardware_access(request: Request, db, mac: str, organization_id: int | None = None):
    user, organizations, selected_org_id, domains = _hardware_scope(request, db, organization_id)
    item = _find_phone_inventory(mac)
    if not item:
        raise HTTPException(404, "Phone hardware was not found in DigiCloud inventory.")
    allowed = {d.domain_name.casefold() for d in domains}
    if not item["domain"] or item["domain"].casefold() not in allowed:
        raise HTTPException(403, "This phone hardware is not available to the selected reseller.")
    return user, organizations, selected_org_id, domains, item

def _available_inventory(rows: list[dict], domain: str) -> list[dict]:
    result = []
    target = str(domain or "").casefold()
    for row in rows:
        view = _phone_inventory_view(row)
        if not view["mac"] or view["assigned"]:
            continue
        if view["domain"] and view["domain"].casefold() != target:
            continue
        result.append(view)
    return sorted(result, key=lambda x: (x["model"].casefold(), x["mac"]))
def _generate_sip_password(length: int = 16) -> str:
    """Generate a readable SIP password for manual device provisioning."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def _normalize_catalog_row(row: dict) -> dict:
    """Normalize both documented and deployed /phones/models response formats.

    Current NetSapiens documentation uses brand/model/brand_model while some
    production systems return device-models-* names. Keep the complete device
    definition because phone_ext/fxs determine how many line assignments NOP
    must render.
    """
    brand = str(row.get("brand") or row.get("device-models-brand") or "").strip()
    api_model = str(row.get("model") or row.get("device-models-model") or "").strip()
    display = str(row.get("brand_model") or row.get("device-models-brand-and-model") or "").strip()
    if not display:
        display = " ".join(part for part in (brand, api_model) if part).strip()
    if not api_model and display:
        if brand and display.casefold().startswith(brand.casefold() + " "):
            api_model = display[len(brand):].strip()
        else:
            api_model = display

    def integer(*names: str) -> int:
        for name in names:
            value = row.get(name)
            if value not in (None, ""):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
        return 0

    return {
        "brand": brand,
        "model": api_model,
        "brand_model": display,
        "portal_view": str(row.get("portal_view") or row.get("device-models-visible-in-portal") or "yes").strip().lower(),
        "device_type": str(row.get("device_type") or row.get("device-models-type") or "Device").strip(),
        "config_format": str(row.get("ndp_syntax") or row.get("device-models-config-format") or "").strip(),
        "phone_ext": integer("phone_ext", "device-models-phone-ext"),
        "fxs": integer("fxs", "device-models-fxs"),
        "fxo": integer("fxo", "device-models-fxo"),
        "trunk": integer("trunk", "device-models-trunk"),
        "description": str(row.get("description") or row.get("device-models-description") or "").strip(),
        "raw": row,
    }


def _model_identity(display_name: str) -> tuple[str, str]:
    display = str(display_name or "").strip()
    if not display:
        return "", ""
    brand, _, model = display.partition(" ")
    return brand.strip(), model.strip()


def _model_line_count(model_row: dict, existing: dict | None = None) -> int:
    candidates = [
        model_row.get("phone_ext"), model_row.get("device-models-phone-ext"),
        model_row.get("fxs"), model_row.get("device-models-fxs"),
    ]
    counts = []
    for value in candidates:
        try:
            counts.append(int(value or 0))
        except (TypeError, ValueError):
            pass
    count = max(counts or [0])
    if existing:
        for index in range(1, 9):
            if existing.get(f"device-provisioning-sip-uri-{index}") not in (None, ""):
                count = max(count, index)
    return max(1, min(count or 1, 8))


def _line_value_to_sip_uri(value: str, domain: str) -> str:
    raw = str(value or "").strip()
    # NetSapiens uses n/a for an available/unassigned hardware line. Treat it
    # exactly like a blank value so NOP never creates sip:n/a@domain.
    if raw.casefold() in {"", "n/a", "na", "none", "unassigned", "available", "-"}:
        return ""
    if raw.lower().startswith("sip:"):
        return raw
    if "@" in raw:
        return f"sip:{raw}"
    return f"sip:{raw}@{domain}"


def _sip_uri_to_extension(value: str) -> str:
    raw = str(value or "").strip()
    if raw.casefold() in {"", "n/a", "na", "none", "unassigned", "available", "-"}:
        return ""
    if raw.lower().startswith("sip:"):
        raw = raw[4:]
    extension = raw.split("@", 1)[0].strip()
    return "" if extension.casefold() in {"n/a", "na", "none", "unassigned", "available", "-"} else extension


def _device_catalog() -> list[dict]:
    try:
        live = NetSapiensPhoneProvisioning().models()
        rows = [_normalize_catalog_row(row) for row in live]
        visible = [row for row in rows if row["portal_view"] in {"yes", "true", "1"}]
        if visible:
            return visible
    except NetSapiensError:
        pass
    path = Path(__file__).resolve().parents[1] / "resources" / "digicloud_device_models.json"
    try:
        legacy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [row for row in (_normalize_catalog_row(item) for item in legacy)
            if row["portal_view"] in {"yes", "true", "1"}]


def _provisioning_scope_org_ids(db, organization_id: int) -> list[int]:
    """Resolve organizations that share the same NetSapiens reseller configuration.

    Managed user domains can be assigned to a customer-facing organization while
    reseller defaults and approved models are maintained on the reseller's primary
    organization.  Treat matching reseller mappings as one provisioning scope.
    """
    settings = db.scalar(select(DigiCloudOrganizationSettings).where(
        DigiCloudOrganizationSettings.organization_id == organization_id
    ))
    reseller = str(settings.netsapiens_reseller or "").strip() if settings else ""
    if not reseller:
        configured = list(db.scalars(select(DigiCloudOrganizationSettings).where(
            DigiCloudOrganizationSettings.active.is_(True),
            DigiCloudOrganizationSettings.netsapiens_reseller != "",
        )).all())
        reseller_names = {str(row.netsapiens_reseller or "").strip() for row in configured if str(row.netsapiens_reseller or "").strip()}
        if len(reseller_names) == 1:
            return list(dict.fromkeys([organization_id, *[row.organization_id for row in configured]]))
        return [organization_id]
    ids = list(db.scalars(select(DigiCloudOrganizationSettings.organization_id).where(
        DigiCloudOrganizationSettings.netsapiens_reseller == reseller,
        DigiCloudOrganizationSettings.active.is_(True),
    )).all())
    return list(dict.fromkeys([organization_id, *ids]))


def _provisioning_context(db, organization_id: int) -> tuple[list[DigiCloudResellerDeviceModel], str]:
    scope_ids = _provisioning_scope_org_ids(db, organization_id)
    models = list(db.scalars(
        select(DigiCloudResellerDeviceModel)
        .where(
            DigiCloudResellerDeviceModel.organization_id.in_(scope_ids),
            DigiCloudResellerDeviceModel.enabled.is_(True),
        )
        .order_by(
            DigiCloudResellerDeviceModel.sort_order,
            DigiCloudResellerDeviceModel.brand,
            DigiCloudResellerDeviceModel.model_name,
        )
    ).all())
    # Deduplicate when the same model is enabled on more than one org in a reseller scope.
    models = list({row.model_name.casefold(): row for row in models}.values())
    catalog = _device_catalog()
    catalog_by_display = {row["brand_model"].casefold(): row for row in catalog}
    catalog_by_api = {row["model"].casefold(): row for row in catalog if row["model"]}
    # Reconcile approvals saved by older builds with the live catalog. This is
    # deliberately case-insensitive because model capitalization differs across
    # NetSapiens releases (for example spa2102 vs SPA2102).
    for approved in models:
        source = catalog_by_display.get(str(approved.model_name or "").casefold())
        if source is None and str(approved.api_model_value or "").strip():
            source = catalog_by_api.get(str(approved.api_model_value).casefold())
        if source:
            approved.model_name = source["brand_model"]
            approved.api_model_value = source["model"]
            approved.brand = source["brand"]
            approved.device_type = source["device_type"]
            approved.config_format = source["config_format"]
    settings_rows = list(db.scalars(select(DigiCloudOrganizationSettings).where(
        DigiCloudOrganizationSettings.organization_id.in_(scope_ids)
    )).all())
    settings_rows.sort(key=lambda row: 0 if row.organization_id == organization_id else 1)
    server = next((str(row.provisioning_server or "").strip() for row in settings_rows
                   if str(row.provisioning_server or "").strip()), "")
    if not server:
        # Safe operational fallback: use the hostname of the configured DigiCloud API server.
        api_url = str(NetSapiensClient().settings.netsapiens_api_url or "").strip()
        parsed = urlparse(api_url if "://" in api_url else f"https://{api_url}")
        server = parsed.hostname or ""
    return models, server


def _provisioning_servers() -> list[dict]:
    """Return live provisionable server profiles in a normalized form."""
    try:
        rows = NetSapiensPhoneProvisioning().servers()
    except NetSapiensError:
        return []
    normalized = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = str(
            row.get("server")
            or row.get("hostname")
            or row.get("name")
            or row.get("ns_api_hostname")
            or row.get("device-provisioning-registration-core-server")
            or row.get("core-server")
            or ""
        ).strip()
        location = str(row.get("location") or "").strip()
        label = str(
            row.get("description")
            or row.get("display_name")
            or row.get("profile")
            or (f"{value} — {location}" if value and location else value)
        ).strip()
        if value and value not in seen:
            seen.add(value)
            normalized.append({"value": value, "label": label or value, "raw": row})
    return normalized


def _default_provisioning_servers() -> list[dict]:
    """Return only server profiles marked or named as defaults.

    NetSapiens deployments are not fully consistent about the default flag, so
    this accepts common boolean/default field names and profiles whose metadata
    contains the word ``default``. If the deployment returns no explicit default
    marker, active/online profiles are used as a safe compatibility fallback.
    """
    servers = _provisioning_servers()
    if not servers:
        return []

    yes_values = {"1", "true", "yes", "y", "on", "default"}
    marker_fields = (
        "default", "is_default", "is-default", "default_server",
        "default-server", "server_default", "server-default",
        "default_profile", "default-profile",
    )
    text_fields = ("name", "location", "geo_group", "postfix", "description", "profile")

    defaults = []
    for server in servers:
        raw = server.get("raw") or {}
        explicitly_default = any(
            str(raw.get(field) or "").strip().casefold() in yes_values
            for field in marker_fields
        )
        named_default = any(
            "default" in str(raw.get(field) or "").strip().casefold()
            for field in text_fields
        )
        if explicitly_default or named_default:
            defaults.append(server)

    if defaults:
        return defaults

    active_values = {"", "active", "online", "up", "enabled", "ok", "ready"}
    active = [
        server for server in servers
        if str((server.get("raw") or {}).get("status") or "").strip().casefold() in active_values
    ]
    return active or servers


def _normalize_mac(value: str) -> str:
    mac = re.sub(r"[^0-9A-Fa-f]", "", value or "").upper()
    if len(mac) != 12:
        raise ValueError("MAC address must contain exactly 12 hexadecimal characters")
    return mac


def _device_view(row: dict) -> dict:
    model = str(row.get("device-models-model") or "").strip()
    mac = str(row.get("device-provisioning-mac-address") or "").strip()
    raw_mac = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    formatted_mac = ":".join(raw_mac[i:i+2] for i in range(0, 12, 2)) if len(raw_mac) == 12 else mac
    device_type = "Device Provisioning" if model or mac else "Manual Provisioning"
    emergency = str(row.get("caller-id-number-emergency") or "[*]")
    return {
        "raw": row,
        "device": row.get("device") or "",
        "device_type": device_type,
        "model": model,
        "mac": formatted_mac,
        "state": row.get("device-sip-registration-state") or "unknown",
        "login": row.get("login-username") or row.get("device-provisioning-username") or "",
        "server": row.get("core-server") or row.get("device-provisioning-registration-core-server") or "",
        "ip": row.get("device-sip-registration-ip-address") or "",
        "user_agent": row.get("device-sip-registration-user-agent") or "",
        "emergency": "Default" if emergency == "[*]" else emergency,
        "emergency_address": row.get("emergency-address-id") or "",
        "line": row.get("device-provisioning-line"),
    }

@router.get("")
async def digicloud_root():
    return RedirectResponse("/digicloud/domains", status_code=303)

@router.get("/phone-numbers", response_class=HTMLResponse)
async def phone_numbers(request: Request, q: str = ""):
    require_permission(request, "digicloud.numbers.read")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        svc = DigiCloudService(db, ctx, request)
        return render(
            request,
            "digicloud/phone_numbers.html",
            numbers=svc.list_numbers(q),
            q=q,
        )


@router.post("/phone-numbers/sync")
async def sync_phone_numbers(request: Request):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        try:
            result = DigiCloudService(db, ctx, request).sync_phone_numbers()
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error("/digicloud/phone-numbers", exc)
        except Exception as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/phone-numbers?error={quote_plus(str(exc))}", 303
            )

    notice = quote_plus(
        f"Sync complete: {result['created']} created, {result['updated']} updated, "
        f"{result['unchanged']} unchanged, {result['reassigned']} reassigned, "
        f"{result['skipped']} skipped"
        + (f", {result['unmatched_domains']} unmatched domains" if result['unmatched_domains'] else "")
    )
    return RedirectResponse(f"/digicloud/phone-numbers?notice={notice}", 303)


@router.get("/phone-numbers/new", response_class=HTMLResponse)
async def new_phone_number(request: Request, organization_id: int | None = None):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        svc = DigiCloudService(db, ctx, request)
        org_id = organization_id or ctx.organization_id
        if ctx.is_staff and not org_id:
            organizations = svc.organizations()
            org_id = organizations[0].id if organizations else None
        domains = svc.number_domains(org_id) if org_id else []
        return render(
            request,
            "digicloud/phone_number_form.html",
            number=None,
            domains=domains,
            organizations=svc.organizations(),
            selected_org_id=org_id,
        )


@router.post("/phone-numbers")
async def create_phone_number_assignment(
    request: Request,
    organization_id: int = Form(...),
    telephone_number: str = Form(...),
    domain_id: int | None = Form(None),
    destination_user: str = Form(""),
    description: str = Form(""),
    treatment: str = Form("available"),
    enabled: str | None = Form(None),
):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        try:
            obj, action = DigiCloudService(db, ctx, request).add_or_move_number_live(
                None, telephone_number, organization_id, domain_id, destination_user,
                description, treatment, bool_form(enabled)
            )
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error("/digicloud/phone-numbers/new", exc)
    return RedirectResponse(
        f"/digicloud/phone-numbers/{obj.id}/manage?notice={quote_plus('Phone number ' + action)}",
        303,
    )


@router.get("/phone-numbers/{number_id}/manage", response_class=HTMLResponse)
async def manage_phone_number(request: Request, number_id: int):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        svc = DigiCloudService(db, ctx, request)
        obj = svc.get_number(number_id)
        return render(
            request,
            "digicloud/phone_number_form.html",
            number=obj,
            domains=svc.number_domains(obj.organization_id),
            organizations=svc.organizations(),
            selected_org_id=obj.organization_id,
            live_settings=svc.live_number_settings(obj),
        )


@router.get("/phone-numbers/{number_id}/delete", response_class=HTMLResponse)
async def delete_phone_number_page(request: Request, number_id: int):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        svc = DigiCloudService(db, ctx, request)
        obj = svc.get_number(number_id)
        return render(
            request,
            "digicloud/phone_number_delete.html",
            number=obj,
        )


@router.post("/phone-numbers/{number_id}/assign")
async def assign_phone_number_live(
    request: Request,
    number_id: int,
    organization_id: int = Form(...),
    telephone_number: str = Form(...),
    domain_id: int | None = Form(None),
    destination_user: str = Form(""),
    description: str = Form(""),
    treatment: str = Form("available"),
    enabled: str | None = Form(None),
):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        try:
            obj, action = DigiCloudService(db, ctx, request).add_or_move_number_live(
                number_id, telephone_number, organization_id, domain_id, destination_user,
                description, treatment, bool_form(enabled)
            )
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error(f"/digicloud/phone-numbers/{number_id}/manage", exc)
    return RedirectResponse(
        f"/digicloud/phone-numbers/{obj.id}/manage?notice={quote_plus('Phone number ' + action)}",
        303,
    )


@router.post("/phone-numbers/{number_id}/delete")
async def delete_phone_number_live(
    request: Request,
    number_id: int,
    confirmation: str = Form(""),
):
    require_permission(request, "digicloud.numbers.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        try:
            telephone_number, old_domain = DigiCloudService(db, ctx, request).delete_number_live(
                number_id, confirmation
            )
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error(f"/digicloud/phone-numbers/{number_id}/delete", exc)
    location = f" from {old_domain.domain_name}" if old_domain else ""
    notice = quote_plus(
        f"{telephone_number} was deleted{location} from DigiCloud and removed from NOP inventory. "
        "The carrier number was not deleted."
    )
    return RedirectResponse(f"/digicloud/phone-numbers?notice={notice}", 303)


@router.get("/domains",response_class=HTMLResponse)
async def domains(request:Request,q:str=""):
    require_permission(request,"digicloud.domains.read"); ctx=context_from_request(request)
    with SessionLocal() as db:
        svc=DigiCloudService(db,ctx,request)
        return render(request,"digicloud/domains.html",domains=svc.list_domains(q),q=q,query=q,status_filter="")

@router.post("/domains/sync")
async def sync_domains(request: Request):
    require_permission(request, "digicloud.domains.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        try:
            result = DigiCloudService(db, ctx, request).sync_domains()
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error("/digicloud/domains", exc)
        except Exception as exc:
            db.rollback()
            return RedirectResponse(f"/digicloud/domains?error={quote_plus(str(exc))}", 303)

    notice = quote_plus(
        f"Sync complete: {result['created']} created, {result['updated']} updated, "
        f"{result['unchanged']} unchanged, {result['reassigned']} reassigned, "
        f"{result['skipped']} skipped"
    )
    return RedirectResponse(f"/digicloud/domains?notice={notice}", 303)

@router.get("/domains/new",response_class=HTMLResponse)
async def new_domain(request:Request,organization_id:int|None=None):
    require_permission(request,"digicloud.domains.manage"); ctx=context_from_request(request)
    with SessionLocal() as db:
        svc=DigiCloudService(db,ctx,request); org_id=organization_id or ctx.organization_id
        return render(request,"digicloud/domain_form.html",domain=None,defaults=svc.settings_for(org_id),organizations=svc.organizations(),selected_org_id=org_id)

@router.post("/domains")
async def create_domain(request:Request,organization_id:int=Form(...),domain_name:str=Form(...),description:str=Form(""),caller_id_name:str=Form(""),caller_id_number:str=Form(""),emergency_caller_id:str=Form(""),area_code:str=Form("803"),time_zone:str=Form("America/New_York"),max_calls:int=Form(10),max_offnet_calls:int=Form(3),recording_enabled:str|None=Form(None),transcription_enabled:str|None=Form(None),transcription_provider:str=Form("Deepgram"),email_from:str=Form("no.reply@digicloudpbx.com"),sync_provider:str|None=Form(None)):
    require_permission(request,"digicloud.domains.manage"); ctx=context_from_request(request)
    with SessionLocal() as db:
        try:
            obj=DigiCloudService(db,ctx,request).create_domain(organization_id,domain_name,sync_provider=bool_form(sync_provider),description=description.strip(),caller_id_name=caller_id_name.strip(),caller_id_number=caller_id_number.strip(),emergency_caller_id=emergency_caller_id.strip(),area_code=area_code.strip(),time_zone=time_zone.strip(),max_calls=max_calls,max_offnet_calls=max_offnet_calls,recording_enabled=bool_form(recording_enabled),transcription_enabled=bool_form(transcription_enabled),transcription_provider=transcription_provider.strip(),email_from=email_from.strip()); db.commit()
        except HTTPException as exc: db.rollback(); return redirect_error("/digicloud/domains/new",exc)
    return RedirectResponse(f"/digicloud/domains/{obj.id}/edit?notice=Domain+created",303)


@router.get("/domains/assignments", response_class=HTMLResponse)
async def domain_assignments(request: Request):
    require_permission(request, "digicloud.settings")
    ctx = require_platform_staff(request)
    if not ctx.is_superuser:
        raise HTTPException(403, "Platform Admin access required")
    with SessionLocal() as db:
        try:
            conflicts, warnings = DigiCloudService(db, ctx, request).domain_assignment_conflicts()
        except HTTPException as exc:
            return redirect_error("/digicloud/domains", exc)
        return render(
            request,
            "digicloud/domain_assignments.html",
            conflicts=conflicts,
            warnings=warnings,
        )


@router.post("/domains/{domain_id}/reassign")
async def reassign_domain(
    request: Request,
    domain_id: int,
    target_organization_id: int = Form(...),
):
    require_permission(request, "digicloud.settings")
    ctx = require_platform_staff(request)
    if not ctx.is_superuser:
        raise HTTPException(403, "Platform Admin access required")
    with SessionLocal() as db:
        try:
            domain, moved, old_org, target_org = DigiCloudService(db, ctx, request).reassign_domain(
                domain_id, target_organization_id
            )
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error("/digicloud/domains/assignments", exc)
        except Exception as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/domains/assignments?error={quote_plus(str(exc))}", 303
            )
    notice = quote_plus(
        f"{domain.domain_name} reassigned from {old_org.name} to {target_org.name}; "
        f"{moved} linked phone number(s) moved"
    )
    return RedirectResponse(f"/digicloud/domains/assignments?notice={notice}", 303)

@router.get("/domains/{domain_id}/edit", response_class=HTMLResponse)
async def edit_domain_page(request: Request, domain_id: int):
    require_permission(request, "digicloud.domains.manage")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        obj = DigiCloudService(db, ctx, request).get_domain(domain_id)
        return render(request, "digicloud/domain_edit.html", domain=obj)


@router.get("/domains/{domain_id}/delete", response_class=HTMLResponse)
async def delete_domain_page(request: Request, domain_id: int):
    require_permission(request, "digicloud.domains.delete")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        obj = DigiCloudService(db, ctx, request).get_domain(domain_id)
        return render(request, "digicloud/domain_delete.html", domain=obj)


@router.get("/domains/{domain_id}")
async def domain_detail(request: Request, domain_id: int):
    require_permission(request, "digicloud.domains.read")
    return RedirectResponse(f"/digicloud/domains/{domain_id}/edit", status_code=303)


@router.post("/domains/{domain_id}")
async def update_domain(request:Request,domain_id:int,description:str=Form(""),caller_id_name:str=Form(""),caller_id_number:str=Form(""),emergency_caller_id:str=Form(""),area_code:str=Form("803"),time_zone:str=Form("America/New_York"),max_calls:int=Form(10),max_offnet_calls:int=Form(3),recording_enabled:str|None=Form(None),transcription_enabled:str|None=Form(None),transcription_provider:str=Form("Deepgram"),email_from:str=Form("")):
    require_permission(request,"digicloud.domains.manage"); ctx=context_from_request(request)
    with SessionLocal() as db:
        try: DigiCloudService(db,ctx,request).update_domain(domain_id,sync_provider=True,description=description.strip(),caller_id_name=caller_id_name.strip(),caller_id_number=caller_id_number.strip(),emergency_caller_id=emergency_caller_id.strip(),area_code=area_code.strip(),time_zone=time_zone.strip(),max_calls=max_calls,max_offnet_calls=max_offnet_calls,recording_enabled=bool_form(recording_enabled),transcription_enabled=bool_form(transcription_enabled),transcription_provider=transcription_provider.strip(),email_from=email_from.strip()); db.commit()
        except HTTPException as exc: db.rollback(); return redirect_error(f"/digicloud/domains/{domain_id}/edit",exc)
    return RedirectResponse(f"/digicloud/domains/{domain_id}/edit?notice=Domain+updated",303)

@router.post("/domains/{domain_id}/delete")
async def delete_domain(request: Request, domain_id: int, confirmation: str = Form(...)):
    require_permission(request, "digicloud.domains.delete")
    ctx = context_from_request(request)
    with SessionLocal() as db:
        try:
            DigiCloudService(db, ctx, request).delete_domain(domain_id, confirmation)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            return redirect_error(f"/digicloud/domains/{domain_id}/delete", exc)
    return RedirectResponse(
        "/digicloud/domains?notice=Domain+and+assigned+numbers+removed+from+DigiCloud+and+NOP.+Carrier+numbers+were+not+deleted",
        303,
    )

@router.get("/numbers",response_class=HTMLResponse)
async def numbers(request:Request,q:str=""):
    require_permission(request,"digicloud.numbers.read"); ctx=context_from_request(request)
    with SessionLocal() as db:
        svc=DigiCloudService(db,ctx,request)
        return render(request,"digicloud/numbers.html",numbers=svc.list_numbers(q),domains=svc.list_domains(),organizations=svc.organizations(),q=q)

@router.post("/numbers")
async def add_number(request:Request,organization_id:int=Form(...),telephone_number:str=Form(...),notes:str=Form("")):
    require_permission(request,"digicloud.numbers.manage"); ctx=context_from_request(request)
    with SessionLocal() as db:
        try: DigiCloudService(db,ctx,request).add_number(organization_id,telephone_number,notes); db.commit()
        except HTTPException as exc: db.rollback(); return redirect_error("/digicloud/numbers",exc)
    return RedirectResponse("/digicloud/numbers?notice=Number+added",303)

@router.post("/numbers/{number_id}/assign")
async def assign_number(request:Request,number_id:int,domain_id:int|None=Form(None)):
    require_permission(request,"digicloud.numbers.manage"); ctx=context_from_request(request)
    with SessionLocal() as db:
        try: DigiCloudService(db,ctx,request).assign_number(number_id,domain_id); db.commit()
        except HTTPException as exc: db.rollback(); return redirect_error("/digicloud/numbers",exc)
    return RedirectResponse("/digicloud/numbers?notice=Assignment+updated",303)

@router.post("/numbers/{number_id}/delete")
async def remove_number(request:Request,number_id:int):
    require_permission(request,"digicloud.numbers.manage"); ctx=context_from_request(request)
    with SessionLocal() as db:
        try: DigiCloudService(db,ctx,request).remove_number(number_id); db.commit()
        except HTTPException as exc: db.rollback(); return redirect_error("/digicloud/numbers",exc)
    return RedirectResponse("/digicloud/numbers?notice=Number+removed",303)

@router.get("/admin/settings",response_class=HTMLResponse)
async def settings(request:Request):
    require_permission(request,"digicloud.settings"); ctx=require_platform_staff(request)
    if not ctx.is_superuser: raise HTTPException(403,"Platform Admin access required")
    with SessionLocal() as db:
        svc=DigiCloudService(db,ctx,request)
        rows=[(org,svc.settings_for(org.id)) for org in svc.organizations()]
        return render(request,"digicloud/settings.html",rows=rows)

@router.post("/admin/settings/{organization_id}")
async def save_settings(request:Request,organization_id:int,netsapiens_reseller:str=Form(""),default_area_code:str=Form("803"),default_time_zone:str=Form("America/New_York"),default_max_calls:int=Form(10),default_max_offnet_calls:int=Form(3),default_recording_enabled:str|None=Form(None),default_transcription_enabled:str|None=Form(None),default_transcription_provider:str=Form("Deepgram"),default_email_from:str=Form("no.reply@digicloudpbx.com"),provisioning_server:str=Form(""),billing_model:str=Form("direct"),platypus_parent_customer_id:str=Form(""),wholesale_rate_group_ids:str=Form(""),default_wholesale_rate_group_id:str=Form(""),active:str|None=Form(None)):
    require_permission(request,"digicloud.settings"); ctx=require_platform_staff(request)
    with SessionLocal() as db:
        try:
            model = billing_model.strip().lower()
            if model not in {"direct", "referral", "wholesale"}: raise HTTPException(400, "Invalid DigiCloud billing model.")
            rate_ids = list(dict.fromkeys(re.findall(r"\d+", wholesale_rate_group_ids)))
            default_rate = default_wholesale_rate_group_id.strip()
            if model == "wholesale" and not platypus_parent_customer_id.strip(): raise HTTPException(400, "Wholesale billing requires a parent Platypus customer ID.")
            if model == "wholesale" and not rate_ids: raise HTTPException(400, "Wholesale billing requires at least one permitted RGID.")
            if default_rate and default_rate not in rate_ids: raise HTTPException(400, "The default wholesale RGID must be in the permitted RGID list.")
            DigiCloudService(db,ctx,request).save_settings(organization_id,netsapiens_reseller=netsapiens_reseller.strip(),default_area_code=default_area_code.strip(),default_time_zone=default_time_zone.strip(),default_max_calls=default_max_calls,default_max_offnet_calls=default_max_offnet_calls,default_recording_enabled=bool_form(default_recording_enabled),default_transcription_enabled=bool_form(default_transcription_enabled),default_transcription_provider=default_transcription_provider.strip(),default_email_from=default_email_from.strip(),provisioning_server=provisioning_server.strip(),billing_model=model,platypus_parent_customer_id=platypus_parent_customer_id.strip(),wholesale_rate_group_ids=json.dumps(rate_ids),default_wholesale_rate_group_id=default_rate,active=bool_form(active)); db.commit()
        except HTTPException as exc: db.rollback(); return redirect_error("/digicloud/admin/settings",exc)
    return RedirectResponse("/digicloud/admin/settings?notice=Defaults+updated",303)

# DigiCloud User Management -------------------------------------------------

@router.get("/users", response_class=HTMLResponse)
async def digicloud_user_management(
    request: Request,
    domain: str | None = None,
    show_hidden: bool = False,
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        domains = allowed_user_domains(db, user)
        selected = None
        if domain:
            selected = require_allowed_domain(db, user, domain)
        elif domains:
            selected = domains[0]

        users = []
        live_error = None
        if selected is not None:
            try:
                users = NetSapiensUsers().list(selected.domain_name)
            except NetSapiensError as exc:
                live_error = str(exc).replace("NetSapiens", "DigiCloud")

        hidden_count = sum(1 for item in users if item.get("hidden"))
        can_show_hidden = bool(user.is_superuser)
        show_hidden = bool(show_hidden and can_show_hidden)
        visible_users = users if show_hidden else [item for item in users if not item.get("hidden")]

        active_count = sum(1 for item in visible_users if item["enabled"] is True)
        disabled_count = sum(1 for item in visible_users if item["enabled"] is False)
        unknown_count = len(visible_users) - active_count - disabled_count

        return render(
            request,
            "digicloud/user_management/domain_selector.html",
            allowed_domains=domains,
            selected_domain=selected,
            users=visible_users,
            total_live_users=len(users),
            hidden_count=hidden_count,
            can_show_hidden=can_show_hidden,
            show_hidden=show_hidden,
            active_count=active_count,
            disabled_count=disabled_count,
            unknown_count=unknown_count,
            live_error=live_error,
        )


@router.get("/users/new", response_class=HTMLResponse)
async def new_digicloud_user(request: Request, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        service = DigiCloudService(db, context_from_request(request), request)
        defaults = service.settings_for(selected.organization_id)
        local_domain = _local_digicloud_domain(db, selected)
        if local_domain is None:
            try:
                service.sync_domains()
                db.flush()
                local_domain = _local_digicloud_domain(db, selected)
                db.commit()
            except HTTPException:
                db.rollback()
        did_error = ""
        live_routes: list[dict] = []
        try:
            live_routes = NetSapiensPhoneNumbers().list_for_domain(selected.domain_name)
        except NetSapiensError as exc:
            did_error = str(exc).replace("NetSapiens", "DigiCloud")
        try:
            live_users = NetSapiensUsers().list(selected.domain_name)
        except NetSapiensError as exc:
            live_users = []
            did_error = str(exc).replace("NetSapiens", "DigiCloud")
        available_dids, did_statuses = _eligible_domain_dids(
            db, local_domain, live_routes, live_users
        )
        try:
            available_phones = _available_inventory(NetSapiensPhoneProvisioning().list_domain_phones(selected.domain_name), selected.domain_name)
        except NetSapiensError:
            available_phones = []
        fixed_platypus_customer_id = request.query_params.get("platypus_customer_id", "").strip()
        fixed_rate_group_id = request.query_params.get("rate_group_id", "").strip()
        return_to = request.query_params.get("return_to", "").strip()
        prefill = {
            "extension": request.query_params.get("extension", "").strip(),
            "first_name": request.query_params.get("first_name", "").strip(),
            "last_name": request.query_params.get("last_name", "").strip(),
            "email": request.query_params.get("email", "").strip(),
        }
        billing_model = str(defaults.billing_model or "direct").strip().lower()
        wholesale_rate_ids: list[str] = []
        if billing_model == "wholesale" and not fixed_platypus_customer_id:
            fixed_platypus_customer_id = str(defaults.platypus_parent_customer_id or "").strip()
            try:
                parsed_rates = json.loads(defaults.wholesale_rate_group_ids or "[]")
                wholesale_rate_ids = [str(value).strip() for value in parsed_rates if str(value).strip()]
            except (TypeError, ValueError):
                wholesale_rate_ids = []
            fixed_rate_group_id = str(defaults.default_wholesale_rate_group_id or "").strip()
            if not fixed_platypus_customer_id or not wholesale_rate_ids:
                raise HTTPException(400, "Wholesale DigiCloud billing is not fully configured for this reseller.")
        displayed_rates = ({rgid: "Wholesale DigiCloud Voice" for rgid in wholesale_rate_ids}
                           if billing_model == "wholesale" else DIGICLOUD_RESIDENTIAL_RATES)
        if fixed_rate_group_id and fixed_rate_group_id not in displayed_rates:
            raise HTTPException(400, "The selected rate is not a supported DigiCloud residential rate.")
        fixed_billing_customer = db.execute(
            select(Customer, ExternalRecordLink)
            .join(ExternalRecordLink, ExternalRecordLink.customer_id == Customer.id)
            .where(
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
                ExternalRecordLink.external_id == fixed_platypus_customer_id,
            )
        ).first() if fixed_platypus_customer_id else None
        if fixed_platypus_customer_id and fixed_billing_customer is None:
            try:
                parent_profile = await CustomerDirectory().get(fixed_platypus_customer_id)
                PlatypusCustomerSync(db, context_from_request(request)).sync(parent_profile)
                db.commit()
                fixed_billing_customer = db.execute(
                    select(Customer, ExternalRecordLink)
                    .join(ExternalRecordLink, ExternalRecordLink.customer_id == Customer.id)
                    .where(
                        ExternalRecordLink.system_name == "platypus",
                        ExternalRecordLink.record_type == "customer",
                        ExternalRecordLink.external_id == fixed_platypus_customer_id,
                    )
                ).first()
            except Exception as exc:
                db.rollback()
                raise HTTPException(400, f"Unable to load the configured parent Platypus account: {exc}") from exc
        if fixed_platypus_customer_id and fixed_billing_customer is None:
            raise HTTPException(404, "The configured parent Platypus account was not found.")
        fixed_billing_customer_label = ""
        if fixed_billing_customer is not None:
            customer, link = fixed_billing_customer
            fixed_billing_customer_label = (
                f"{customer.name} · NOP {customer.customer_number} · Platypus #{link.external_id}"
            )
        return render(
            request,
            "digicloud/user_management/user_add.html",
            selected_domain=selected,
            defaults=defaults,
            available_phones=available_phones,
            available_dids=available_dids,
            did_statuses=did_statuses,
            did_error=did_error,
            fixed_billing_customer_label=fixed_billing_customer_label,
            residential_rates=displayed_rates,
            fixed_platypus_customer_id=fixed_platypus_customer_id,
            fixed_rate_group_id=fixed_rate_group_id,
            return_to=return_to,
            billing_model=billing_model,
            prefill=prefill,
        )


@router.get("/users/billing-customers/search")
def search_digicloud_billing_customers(request: Request, q: str = ""):
    """Return a small, searchable set of active Platypus-linked NOP customers."""
    user = require_user_management_access(request)
    query_text = q.strip()
    if len(query_text) < 2:
        return {"customers": []}
    with SessionLocal() as db:
        pattern = f"%{query_text}%"
        statement = (
            select(Customer, ExternalRecordLink)
            .join(ExternalRecordLink, ExternalRecordLink.customer_id == Customer.id)
            .where(
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
                Customer.status == "active",
                or_(
                    Customer.name.ilike(pattern),
                    Customer.customer_number.ilike(pattern),
                    Customer.billing_email.ilike(pattern),
                    Customer.billing_phone.ilike(pattern),
                    ExternalRecordLink.external_id.ilike(pattern),
                    ExternalRecordLink.external_account_number.ilike(pattern),
                ),
            )
            .order_by(Customer.name)
            .limit(20)
        )
        if not user.organization.is_staff:
            statement = statement.where(or_(
                Customer.owner_organization_id == user.organization_id,
                Customer.servicing_organization_id == user.organization_id,
            ))
        rows = db.execute(statement).all()
        return {
            "customers": [
                {
                    "platypus_customer_id": str(link.external_id),
                    "local_customer_id": customer.id,
                    "customer_number": customer.customer_number,
                    "name": customer.name,
                    "label": f"{customer.name} · NOP {customer.customer_number} · Platypus #{link.external_id}",
                }
                for customer, link in rows
            ]
        }


@router.post("/users/new")
async def create_digicloud_user(
    request: Request,
    domain: str = Form(...),
    extension: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    department: str = Form(""),
    caller_id_name: str = Form(""),
    caller_id_number: str = Form(""),
    emergency_caller_id: str = Form(""),
    time_zone: str = Form("US/Eastern"),
    area_code: str = Form("803"),
    voicemail_pin: str = Form(""),
    voicemail_enabled: str | None = Form(None),
    voicemail_notification_enabled: str | None = Form(None),
    voicemail_notification_email: str = Form(""),
    voicemail_email_type: str = Form("attachment"),
    voicemail_after_notification: str = Form("trash"),
    device_setup: str = Form("none"),
    inventory_mac: str = Form(""),
    platypus_customer_id: str = Form(...),
    residential_rate_group_id: str = Form(...),
    billing_mac: str = Form(""),
    return_to: str = Form(""),
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        org_settings = DigiCloudService(db, context_from_request(request), request).settings_for(selected.organization_id)
        billing_model = str(org_settings.billing_model or "direct").strip().lower()
        try:
            platypus_customer_id, residential_rate_group_id, allowed_wholesale_rates = (
                _resolve_billing_target(
                    org_settings,
                    platypus_customer_id,
                    residential_rate_group_id,
                )
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        clean_extension = "".join(ch for ch in extension if ch.isdigit())
        api = NetSapiensUsers()
        billing_result = None
        sip_password: str | None = None
        provisioning_server = ""
        safe_return = return_to if return_to.startswith("/customers/") else ""
        emergency_setup_url = (
            f"/digicloud/users/{quote_plus(clean_extension)}/911"
            f"?domain={quote_plus(selected.domain_name)}"
            + (f"&return_to={quote_plus(safe_return)}" if safe_return else "")
        )
        try:
            # Validate all local billing inputs before making the irreversible
            # DigiCloud create call.
            if device_setup not in {"none", "inventory", "manual"}:
                raise ValueError("Select a valid device setup option.")
            if device_setup == "inventory":
                clean_billing_mac = normalize_mac(inventory_mac)
            else:
                clean_billing_mac = normalize_mac(billing_mac, required=False)
            if len(clean_extension) != 10:
                raise ValueError("Residential and business voice subscribers require a 10-digit phone number/extension.")
            local_domain = _local_digicloud_domain(db, selected)
            if local_domain is None:
                # Access has already been verified against the live reseller.
                # Create/restore the local operational row instead of forcing a
                # separate domain-sync step before every user provision.
                local_domain = _ensure_local_digicloud_domain(db, selected)
            if billing_model != "wholesale" and residential_rate_group_id.strip() not in DIGICLOUD_RESIDENTIAL_RATES:
                raise ValueError("Select a supported DigiCloud residential rate.")
            linked_customer = db.scalar(select(ExternalRecordLink).where(
                ExternalRecordLink.system_name == "platypus",
                ExternalRecordLink.record_type == "customer",
                ExternalRecordLink.external_id == platypus_customer_id.strip(),
            ))
            if linked_customer is None:
                raise ValueError("Select a Platypus-linked NOP customer.")
            existing = api.list(selected.domain_name)
            available_dids, _ = _eligible_domain_dids(
                db,
                local_domain,
                NetSapiensPhoneNumbers().list_for_domain(selected.domain_name),
                existing,
            )
            existing_user = next((
                row for row in existing
                if clean_extension in {
                    str(row.get("username") or ""),
                    str(row.get("extension") or ""),
                }
            ), None)
            if existing_user is None and clean_extension not in available_dids:
                raise ValueError(
                    f"DID {clean_extension} is not currently available in {selected.domain_name}. "
                    "Sync or add it under DigiCloud Phone Numbers first."
                )
            subscriber_key = f"{clean_extension}@{selected.domain_name}"
            existing_local_service = db.scalar(select(CustomerService).where(
                CustomerService.customer_id == linked_customer.customer_id,
                CustomerService.source_system == "digicloud",
                CustomerService.service_identifier == subscriber_key,
                CustomerService.status != "cancelled",
            ))
            repair_crid = str(existing_local_service.source_rate_id or "").strip() if existing_local_service else ""
            submitted = {
                "extension": clean_extension,
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip(),
                "department": department.strip(),
                "caller_id_name": caller_id_name.strip(),
                "caller_id_number": caller_id_number.strip() or clean_extension,
                "emergency_caller_id": clean_extension,
                "time_zone": time_zone.strip(),
                "language": "en_US",
                "area_code": area_code.strip(),
                "voicemail_pin": voicemail_pin.strip(),
                "voicemail_enabled": bool_form(voicemail_enabled),
                "voicemail_notification_enabled": bool_form(voicemail_notification_enabled),
                "voicemail_notification_email": voicemail_notification_email.strip() or email.strip(),
                "voicemail_email_type": voicemail_email_type.strip() or "attachment",
                "voicemail_after_notification": voicemail_after_notification.strip() or "trash",
                "dial_plan": selected.domain_name,
            }
            digicloud_created = existing_user is None
            if digicloud_created:
                api.create(selected.domain_name, submitted)

            # The DID already exists in the live domain inventory as Available.
            # Convert that route to the new user after the user exists.
            local_number = db.scalar(select(DigiCloudPhoneNumber).where(
                DigiCloudPhoneNumber.telephone_number == clean_extension
            ))
            try:
                NetSapiensPhoneNumbers().update_in_domain(
                    selected.domain_name,
                    clean_extension,
                    destination_user=clean_extension,
                    description=f"{first_name.strip()} {last_name.strip()}".strip(),
                    treatment="user",
                    enabled=True,
                )
                if local_number is None:
                    local_number = DigiCloudPhoneNumber(
                        organization_id=selected.organization_id,
                        telephone_number=clean_extension,
                    )
                    db.add(local_number)
                elif local_number.organization_id != selected.organization_id:
                    number_domain = str(
                        local_number.domain.domain_name if local_number.domain else ""
                    ).strip().lower().rstrip(".")
                    if number_domain != selected.domain_name:
                        raise ValueError("The selected DID belongs to another NOP organization.")
                    # The live reseller is authoritative for this approved
                    # domain. Repair stale local ownership left by an older
                    # import instead of blocking provisioning.
                    local_number.organization_id = selected.organization_id
                local_number.domain_id = local_domain.id
                local_number.status = "assigned"
                local_number.notes = f"{first_name.strip()} {last_name.strip()}".strip()
                db.flush()
            except (NetSapiensError, ValueError) as did_exc:
                # Avoid leaving a brand-new unlinked user behind when the DID
                # assignment fails. Existing-user repair attempts are retained.
                if digicloud_created:
                    try:
                        api.delete(selected.domain_name, clean_extension)
                    except Exception:
                        pass
                raise ValueError(f"Unable to assign the DID: {did_exc}") from did_exc

            # Record the live DigiCloud subscriber in NOP before device,
            # billing, and 911 work continues. Those downstream systems may
            # fail independently; keeping a pending operational record makes
            # the incomplete order visible and recoverable from the customer.
            local_service = db.scalar(select(CustomerService).where(
                CustomerService.customer_id == linked_customer.customer_id,
                CustomerService.source_system == "digicloud",
                CustomerService.service_identifier == subscriber_key,
            ))
            if local_service is None:
                local_service = CustomerService(
                    customer_id=linked_customer.customer_id,
                    service_type="phone",
                    service_name="DigiCloud Residential Subscriber",
                    service_identifier=subscriber_key,
                    source_system="digicloud",
                )
                db.add(local_service)
            local_service.status = "pending"
            local_service.quantity = 1
            local_service.managed_by_source = True
            local_service.source_rate_code = residential_rate_group_id.strip()
            local_service.source_snapshot_json = json.dumps({
                "domain": selected.domain_name,
                "extension": clean_extension,
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip(),
                "platypus_customer_id": platypus_customer_id.strip(),
                "rgid": residential_rate_group_id.strip(),
                "did_inventory_linked": True,
                "legacy_911_address_status": "required_pending",
                "provisioning_status": "pending_billing_and_911",
                "billing_model": billing_model,
                "operating_organization_id": selected.organization_id,
            }, sort_keys=True)
            db.commit()

            # Hardware inventory and SIP user-device connections are separate
            # DigiCloud objects. Create the user first, then optionally assign an
            # existing unassigned MAC inventory record or create manual credentials.
            _, provisioning_server = _provisioning_context(db, selected.organization_id)
            device_event = {"setup": "none" if digicloud_created else "existing-user-billing-repair"}
            if digicloud_created and device_setup == "inventory":
                normalized_mac = _normalize_mac(inventory_mac)
                if not normalized_mac:
                    raise ValueError("Select an available phone from DigiCloud inventory.")
                inventory_rows = [_phone_inventory_view(row) for row in NetSapiensPhoneProvisioning().list_phones()]
                inventory = next((row for row in inventory_rows if row["mac"] == normalized_mac), None)
                if inventory is None or inventory["assigned"]:
                    raise ValueError("The selected phone is no longer available in DigiCloud inventory.")
                server = inventory["server"] or provisioning_server
                if not server:
                    raise ValueError("No preferred server is configured for the selected inventory phone.")
                provider_response = NetSapiensPhoneProvisioning().update_phone(
                    mac=normalized_mac, server=server, domain=selected.domain_name,
                    subscriber_name=clean_extension, transport=inventory["transport"],
                    notes=inventory["notes"],
                    line_assignments=[f"sip:{clean_extension}@{selected.domain_name}"],
                )
                device_event = {"setup": "inventory", "mac": normalized_mac,
                                "model": inventory["model"], "provider_response": provider_response}
            elif digicloud_created and device_setup == "manual":
                if not provisioning_server:
                    raise ValueError("No DigiCloud provisioning/core server is configured for this reseller.")
                sip_password = _generate_sip_password()
                provider_response = NetSapiensDevices().create_manual(
                    selected.domain_name, clean_extension,
                    {
                        "device": clean_extension, "user": clean_extension,
                        "domain": selected.domain_name,
                        "device-sip-registration-uri": f"sip:{clean_extension}@{selected.domain_name}",
                        "device-sip-registration-password": sip_password,
                        "device-sip-registration-core-server": provisioning_server,
                        "login-username": f"{clean_extension}@{selected.domain_name}",
                        "caller-id-number-emergency": "[*]",
                        "device-force-notify-new-voicemails-enabled": "no",
                        "device-level-call-recording-enabled": "no",
                        "device-push-enabled": "no",
                        "device-sip-nat-traversal-enabled": "automatic",
                    },
                )
                device_event = {"setup": "manual", "device": clean_extension,
                                "provisioning_server": provisioning_server}

            # DigiCloud is provisioned first. Platypus then receives the selected
            # residential rate and the Digital Phone service discovered from that
            # assigned rate's live service tree.
            try:
                billing_result = await provision_residential_billing(
                    PlatypusClient(),
                    customer_id=platypus_customer_id.strip(),
                    rate_group_id=residential_rate_group_id.strip(),
                    phone_number=clean_extension,
                    mac_address=clean_billing_mac,
                    voicemail_pin=voicemail_pin.strip(),
                    voicemail_enabled=bool_form(voicemail_enabled),
                    voicemail_email_enabled=bool_form(voicemail_notification_enabled),
                    email_address=voicemail_notification_email.strip() or email.strip(),
                    domain=selected.domain_name,
                    reseller_name=str(org_settings.netsapiens_reseller or "NTInet"),
                    allowed_rate_group_ids=(allowed_wholesale_rates if billing_model == "wholesale" else None),
                    existing_crid=repair_crid,
                )
            except (ValueError, PlatypusAPIError, DigiCloudBillingProvisionError) as billing_exc:
                try:
                    pending_snapshot = json.loads(local_service.source_snapshot_json or "{}")
                except (TypeError, ValueError):
                    pending_snapshot = {}
                pending_snapshot.update({
                    "billing_error": str(billing_exc),
                    "billing_crid": getattr(billing_exc, "crid", ""),
                    "provisioning_status": "billing_incomplete_911_pending",
                })
                local_service.source_snapshot_json = json.dumps(pending_snapshot, sort_keys=True)
                AuditService(db, request, context_from_request(request)).record(
                    "digicloud.user.billing_incomplete", "digicloud_user",
                    f"{clean_extension}@{selected.domain_name}",
                    f"DigiCloud user created, but Platypus billing is incomplete: {billing_exc}",
                    module="digicloud", organization_id=selected.organization_id,
                    event_data={
                        "customer_id": platypus_customer_id,
                        "rgid": residential_rate_group_id,
                        "mac": clean_billing_mac,
                        "billing_crid": getattr(billing_exc, "crid", ""),
                        "submitted_user": {
                            key: value for key, value in submitted.items()
                            if key != "voicemail_pin"
                        },
                        "digicloud_created": digicloud_created,
                    },
                )
                db.commit()
                if sip_password:
                    return render(
                        request,
                        "digicloud/user_management/manual_credentials.html",
                        domain=domain,
                        extension=clean_extension,
                        sip_username=f"{clean_extension}@{domain}",
                        sip_password=sip_password,
                        provisioning_server=provisioning_server,
                        next_url=emergency_setup_url,
                        return_to="",
                        billing_error=str(billing_exc),
                        emergency_status="Required — continue to assign the 911 address.",
                        caller_name=f"{first_name.strip()} {last_name.strip()}".strip(),
                    )
                return RedirectResponse(
                    emergency_setup_url
                    + "&billing_error="
                    + quote_plus(str(billing_exc)),
                    303,
                )

            # Persist the operational relationship in NOP so the customer
            # profile can resolve this exact DigiCloud subscriber independently
            # of subsequent Platypus display-name or service-tree changes.
            local_service.status = "active"
            local_service.quantity = 1
            local_service.source_rate_id = str(billing_result.get("crid") or "")
            local_service.source_rate_code = residential_rate_group_id.strip()
            local_service.managed_by_source = True
            local_service.source_snapshot_json = json.dumps({
                "domain": selected.domain_name,
                "extension": clean_extension,
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip(),
                "mac_address": billing_result.get("mac_address") or clean_billing_mac,
                "platypus_customer_id": platypus_customer_id.strip(),
                "rgid": residential_rate_group_id.strip(),
                "crid": billing_result.get("crid"),
                "service_type_id": billing_result.get("service_type_id") or "",
                "service_data_id": billing_result.get("service_data_id"),
                "did_inventory_linked": True,
                "legacy_911_address_status": "required_pending",
                "provisioning_status": "911_pending",
                "billing_model": billing_model,
                "operating_organization_id": selected.organization_id,
            }, sort_keys=True)

            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.create",
                "digicloud_user",
                f"{clean_extension}@{selected.domain_name}",
                ("Created" if digicloud_created else "Repaired billing for existing")
                + f" DigiCloud user {first_name.strip()} {last_name.strip()} ({clean_extension}) in {selected.domain_name}",
                module="digicloud",
                organization_id=selected.organization_id,
                event_data={
                    "domain": selected.domain_name,
                    "username": clean_extension,
                    "email": email.strip(),
                    "department": department.strip(),
                    "device_setup": device_event,
                    "platypus_billing": billing_result,
                },
            )
            db.commit()
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/new?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
    if sip_password:
        return render(
            request,
            "digicloud/user_management/manual_credentials.html",
            domain=domain,
            extension=clean_extension,
            sip_username=f"{clean_extension}@{domain}",
            sip_password=sip_password,
            provisioning_server=provisioning_server,
            next_url=emergency_setup_url,
            return_to=safe_return,
            billing_error="",
            emergency_status="Required — continue to assign the 911 address.",
            caller_name=f"{first_name.strip()} {last_name.strip()}".strip(),
        )
    return RedirectResponse(emergency_setup_url, 303)


@router.get("/users/{username}/911", response_class=HTMLResponse)
async def configure_digicloud_user_911(
    request: Request,
    username: str,
    domain: str,
    return_to: str = "",
    billing_error: str = "",
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users?domain={quote_plus(selected.domain_name)}"
                f"&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
        if profile.get("hidden"):
            raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
        emergency_did = re.sub(
            r"\D", "", str(profile.get("emergency_caller_id") or username)
        )
        emergency_did_configured = bool(profile.get("emergency_caller_id_configured"))
        current_address = {}
        address_error = ""
        address_source = "none"
        emergency_endpoint_found = False
        emergency_provisioned = False
        try:
            current_address = NetSapiensEmergencyAddresses().endpoint_for_did(
                selected.domain_name, emergency_did
            )
            emergency_endpoint_found = bool(current_address.get("callback_number"))
            # The endpoint-list API proves that an endpoint record exists, but
            # it exposes no carrier-completion status. Never infer provisioned.
            emergency_provisioned = False
            if emergency_endpoint_found:
                address_source = "digicloud_endpoint"
        except NetSapiensError as exc:
            address_error = str(exc).replace("NetSapiens", "DigiCloud")
        if address_source != "digicloud_endpoint":
            local_service = db.scalar(select(CustomerService).where(
                CustomerService.source_system == "digicloud",
                CustomerService.service_identifier == f"{username}@{selected.domain_name}",
            ))
            if local_service is not None:
                try:
                    snapshot = json.loads(local_service.source_snapshot_json or "{}")
                except (TypeError, ValueError):
                    snapshot = {}
                fallback = snapshot.get("legacy_911_address")
                if isinstance(fallback, dict) and fallback.get("address_line_1"):
                    current_address = fallback
                    address_source = "nop_snapshot"
        return render(
            request,
            "digicloud/user_management/911_setup.html",
            selected_domain=selected,
            profile=profile,
            username=username,
            emergency_did=emergency_did,
            emergency_did_configured=emergency_did_configured,
            emergency_endpoint_found=emergency_endpoint_found,
            emergency_provisioned=emergency_provisioned,
            return_to=return_to if return_to.startswith("/customers/") else "",
            billing_error=billing_error,
            values=current_address,
            current_address_id="",
            has_current_address=bool(current_address.get("address_line_1")),
            address_source=address_source,
            address_error=address_error,
            error="",
        )


@router.post("/users/{username}/911", response_class=HTMLResponse)
async def validate_digicloud_user_911(
    request: Request,
    username: str,
    domain: str = Form(...),
    caller_name: str = Form(...),
    address_line_1: str = Form(...),
    address_line_2: str = Form(""),
    city: str = Form(...),
    state: str = Form(...),
    postal_code: str = Form(...),
    emergency_address_id: str = Form(""),
    address_source: str = Form("none"),
    return_to: str = Form(""),
):
    user = require_user_management_access(request)
    safe_return = return_to if return_to.startswith("/customers/") else ""
    safe_address_source = address_source if address_source in {"digicloud_endpoint", "nop_snapshot", "none"} else "none"
    values = {
        "caller_name": caller_name.strip(),
        "address_line_1": address_line_1.strip(),
        "address_line_2": address_line_2.strip(),
        "city": city.strip(),
        "state": state.strip().upper(),
        "postal_code": postal_code.strip(),
    }
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        profile = {}
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            if profile.get("hidden"):
                raise ValueError(f"Protected DigiCloud user: {profile.get('hidden_reason')}")
            if not profile.get("emergency_caller_id_configured"):
                raise ValueError("The DigiCloud user does not have an explicitly configured emergency caller ID.")
            emergency_did = re.sub(
                r"\D", "", str(profile.get("emergency_caller_id") or username)
            )
            if len(emergency_did) != 10:
                raise ValueError("The DigiCloud user does not have a valid 10-digit emergency DID.")

            address_payload = {
                **values,
                "emergency_address_id": emergency_address_id.strip(),
                "address_name": f"911 - {emergency_did}",
                "location_description": "Service address",
                "country": "US",
            }
            provider = NetSapiensEmergencyAddresses()
            validated = provider.validate(selected.domain_name, address_payload)
            corrected = provider.address_view(validated)
            address_id = corrected.get("emergency_address_id", "").strip()
            if not address_id:
                raise ValueError("DigiCloud did not return an emergency address ID.")

            local_service = db.scalar(select(CustomerService).where(
                CustomerService.source_system == "digicloud",
                CustomerService.service_identifier == f"{username}@{selected.domain_name}",
            ))
            if local_service is not None:
                try:
                    snapshot = json.loads(local_service.source_snapshot_json or "{}")
                except (TypeError, ValueError):
                    snapshot = {}
                snapshot.update({
                    "emergency_did": emergency_did,
                    "emergency_address_id": address_id,
                    "legacy_911_address_status": "validated_in_nop_pending_digicloud",
                    "legacy_911_address": corrected,
                    "provisioning_status": "911_pending_assignment",
                })
                local_service.source_snapshot_json = json.dumps(snapshot, sort_keys=True)

            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.911.validate",
                "digicloud_user",
                f"{username}@{selected.domain_name}",
                f"Validated emergency address {address_id}; DigiCloud assignment is still pending",
                module="digicloud",
                organization_id=selected.organization_id,
                event_data={
                    "domain": selected.domain_name,
                    "username": username,
                    "emergency_did": emergency_did,
                    "emergency_address_id": address_id,
                },
            )
            db.commit()
            return render(
                request,
                "digicloud/user_management/911_confirm.html",
                selected_domain=selected,
                profile=profile,
                username=username,
                emergency_did=emergency_did,
                return_to=safe_return,
                values=corrected,
                emergency_address_id=address_id,
                existing_address_id=(
                    emergency_did if safe_address_source == "digicloud_endpoint" else ""
                ),
                error="",
            )
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return render(
                request,
                "digicloud/user_management/911_setup.html",
                status_code=400,
                selected_domain=selected,
                profile=profile,
                username=username,
                emergency_did=str(profile.get("emergency_caller_id") or username),
                emergency_did_configured=bool(profile.get("emergency_caller_id_configured")),
                emergency_endpoint_found=safe_address_source == "digicloud_endpoint",
                emergency_provisioned=False,
                return_to=safe_return,
                billing_error="",
                values=values,
                current_address_id=emergency_address_id.strip(),
                has_current_address=bool(emergency_address_id.strip()),
                address_source=safe_address_source,
                address_error="",
                error=str(exc).replace("NetSapiens", "DigiCloud"),
            )


@router.post("/users/{username}/911/assign", response_class=HTMLResponse)
async def assign_digicloud_user_911(
    request: Request,
    username: str,
    domain: str = Form(...),
    caller_name: str = Form(...),
    address_line_1: str = Form(...),
    address_line_2: str = Form(""),
    city: str = Form(...),
    state: str = Form(...),
    postal_code: str = Form(...),
    emergency_address_id: str = Form(...),
    existing_address_id: str = Form(""),
    return_to: str = Form(""),
):
    user = require_user_management_access(request)
    safe_return = return_to if return_to.startswith("/customers/") else ""
    values = {
        "caller_name": caller_name.strip(),
        "address_line_1": address_line_1.strip(),
        "address_line_2": address_line_2.strip(),
        "city": city.strip(),
        "state": state.strip().upper(),
        "postal_code": postal_code.strip(),
        "country": "US",
    }
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        profile = {}
        emergency_did = username
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            if profile.get("hidden"):
                raise ValueError(f"Protected DigiCloud user: {profile.get('hidden_reason')}")
            if not profile.get("emergency_caller_id_configured"):
                raise ValueError("The DigiCloud user does not have an explicitly configured emergency caller ID.")
            emergency_did = re.sub(
                r"\D", "", str(profile.get("emergency_caller_id") or username)
            )
            if len(emergency_did) != 10:
                raise ValueError("The DigiCloud user does not have a valid 10-digit emergency DID.")

            provider = NetSapiensEmergencyAddresses()
            validated = provider.validate(selected.domain_name, {
                **values,
                "emergency_address_id": emergency_address_id.strip(),
                "address_name": f"911 - {emergency_did}",
                "location_description": "Service address",
            })
            existing_endpoint = provider.endpoint_for_did(selected.domain_name, emergency_did)
            if existing_endpoint:
                provider.update_endpoint(
                    selected.domain_name,
                    emergency_did,
                    validated,
                )
            else:
                provider.create_endpoint(
                    selected.domain_name,
                    emergency_did,
                    validated,
                )

            verified = provider.endpoint_for_did(selected.domain_name, emergency_did)
            expected = provider.address_view(validated)
            comparable_fields = ("address_line_1", "city", "state", "postal_code")
            address_matches = all(
                re.sub(r"[^A-Z0-9]", "", str(verified.get(field) or "").upper())
                == re.sub(r"[^A-Z0-9]", "", str(expected.get(field) or "").upper())
                for field in comparable_fields
            )
            if (
                verified.get("callback_number") != emergency_did
                or not address_matches
            ):
                raise ValueError(
                    "DigiCloud accepted the save request, but NOP could not read back the exact "
                    "callback DID and corrected address from the legacy 911 endpoint. NOP did "
                    "not mark the request as submitted."
                )
            address_id = emergency_did

            local_service = db.scalar(select(CustomerService).where(
                CustomerService.source_system == "digicloud",
                CustomerService.service_identifier == f"{username}@{selected.domain_name}",
            ))
            if local_service is not None:
                try:
                    snapshot = json.loads(local_service.source_snapshot_json or "{}")
                except (TypeError, ValueError):
                    snapshot = {}
                snapshot.update({
                    "emergency_did": emergency_did,
                    "emergency_address_id": address_id,
                    "legacy_911_address_status": "submitted_pending_carrier_confirmation",
                    "legacy_911_address": verified,
                    "provisioning_status": "911_pending_carrier_confirmation",
                })
                local_service.source_snapshot_json = json.dumps(snapshot, sort_keys=True)

            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.911.update" if existing_endpoint else "digicloud.user.911.assign",
                "digicloud_user",
                f"{username}@{selected.domain_name}",
                f"Saved DigiCloud legacy 911 endpoint DID {emergency_did}",
                module="digicloud",
                organization_id=selected.organization_id,
                event_data={
                    "domain": selected.domain_name,
                    "username": username,
                    "emergency_did": emergency_did,
                    "emergency_address_id": address_id,
                    "verified_legacy_911_endpoint_record": True,
                    "carrier_completion_confirmed": False,
                },
            )
            db.commit()
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return render(
                request,
                "digicloud/user_management/911_confirm.html",
                status_code=400,
                selected_domain=selected,
                profile=profile,
                username=username,
                emergency_did=emergency_did,
                return_to=safe_return,
                values=values,
                emergency_address_id=emergency_address_id.strip(),
                existing_address_id=existing_address_id.strip(),
                error=str(exc).replace("NetSapiens", "DigiCloud"),
            )

    notice = quote_plus(
        "911 endpoint update was submitted to DigiCloud; carrier provisioning is unconfirmed."
        if existing_endpoint
        else "911 endpoint was submitted to DigiCloud; carrier provisioning is unconfirmed."
    )
    if safe_return:
        separator = "&" if "?" in safe_return else "?"
        return RedirectResponse(f"{safe_return}{separator}message={notice}", 303)
    return RedirectResponse(
        f"/digicloud/users?domain={quote_plus(domain)}&notice={notice}", 303
    )


@router.get("/users/{username}/edit", response_class=HTMLResponse)
async def edit_digicloud_user(request: Request, username: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
        if profile.get("hidden"):
            raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
        return render(
            request,
            "digicloud/user_management/profile_edit.html",
            selected_domain=selected,
            profile=profile,
            can_inspect=bool(user.is_superuser),
        )


@router.get("/users/{username}/delete", response_class=HTMLResponse)
async def delete_digicloud_user_page(request: Request, username: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
        if profile.get("hidden"):
            raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
        return render(
            request,
            "digicloud/user_management/user_delete.html",
            selected_domain=selected,
            profile=profile,
        )


@router.post("/users/{username}/delete")
async def delete_digicloud_user(
    request: Request,
    username: str,
    domain: str = Form(...),
    confirmation: str = Form(...),
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        api = NetSapiensUsers()
        try:
            profile = api.get(selected.domain_name, username)
            if profile.get("hidden"):
                raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")

            expected = str(profile.get("username") or username).strip()
            if confirmation.strip().lower() != expected.lower():
                raise ValueError(f"Type {expected} exactly to confirm deletion.")

            subscriber_key = f"{expected}@{selected.domain_name}"
            linked_service = db.scalar(select(CustomerService).where(
                CustomerService.source_system == "digicloud",
                CustomerService.service_identifier == subscriber_key,
                CustomerService.status == "active",
            ))
            billing_snapshot = {}
            if linked_service:
                try:
                    billing_snapshot = json.loads(linked_service.source_snapshot_json or "{}")
                except (TypeError, ValueError):
                    billing_snapshot = {}
                emergency_did = str(
                    billing_snapshot.get("emergency_did")
                    or profile.get("emergency_caller_id")
                    or expected
                ).strip()
                existing_911 = NetSapiensEmergencyAddresses().endpoint_for_did(
                    selected.domain_name, emergency_did
                )
                if existing_911:
                    linked_service.status = "provider_cleanup_required"
                    linked_service.notes = (
                        "Deletion stopped before removing the DigiCloud subscriber because a "
                        "linked Legacy 911 endpoint still exists and no supported removal "
                        "operation is configured."
                    )
                    AuditService(db, request, context_from_request(request)).record(
                        "digicloud.user.provider_cleanup_required",
                        "digicloud_user",
                        subscriber_key,
                        linked_service.notes,
                        module="digicloud",
                        organization_id=selected.organization_id,
                        event_data={
                            "domain": selected.domain_name,
                            "username": expected,
                            "emergency_did": emergency_did,
                        },
                    )
                    db.commit()
                    return RedirectResponse(
                        f"/digicloud/users?domain={quote_plus(domain)}&error={quote_plus(linked_service.notes)}",
                        303,
                    )
            api.delete(selected.domain_name, username)
            if linked_service:
                billing_customer_id = str(billing_snapshot.get("platypus_customer_id") or "").strip()
                billing_crid = str(billing_snapshot.get("crid") or linked_service.source_rate_id or "").strip()
                if not billing_customer_id or not billing_crid:
                    linked_service.status = "billing_cleanup_required"
                    linked_service.notes = "DigiCloud user deleted, but the linked Platypus customer ID or CRID is missing."
                    AuditService(db, request, context_from_request(request)).record(
                        "digicloud.user.billing_cleanup_required", "digicloud_user", subscriber_key,
                        linked_service.notes, module="digicloud", organization_id=selected.organization_id,
                    )
                    db.commit()
                    return RedirectResponse(
                        f"/digicloud/users?domain={quote_plus(domain)}&error={quote_plus(linked_service.notes)}", 303
                    )
                try:
                    await PlatypusClient().delete_rate(billing_customer_id, billing_crid)
                except PlatypusAPIError as exc:
                    linked_service.status = "billing_cleanup_required"
                    linked_service.notes = f"DigiCloud user deleted; Platypus rate cleanup failed: {exc}"
                    AuditService(db, request, context_from_request(request)).record(
                        "digicloud.user.billing_cleanup_required", "digicloud_user", subscriber_key,
                        linked_service.notes, module="digicloud", organization_id=selected.organization_id,
                        event_data={"platypus_customer_id": billing_customer_id, "crid": billing_crid},
                    )
                    db.commit()
                    return RedirectResponse(
                        f"/digicloud/users?domain={quote_plus(domain)}&error={quote_plus(linked_service.notes)}", 303
                    )
                linked_service.status = "cancelled"
                linked_service.notes = "DigiCloud subscriber and linked Platypus rate/service removed."
            display_name = profile.get("display_name") or expected
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.delete",
                "digicloud_user",
                f"{username}@{selected.domain_name}",
                f"Deleted DigiCloud user {display_name} ({username}) from {selected.domain_name}",
                module="digicloud",
                organization_id=selected.organization_id,
                event_data={
                    "domain": selected.domain_name,
                    "username": username,
                    "extension": profile.get("extension"),
                    "display_name": display_name,
                    "email": profile.get("email"),
                    "platypus_customer_id": billing_snapshot.get("platypus_customer_id"),
                    "crid": billing_snapshot.get("crid"),
                },
            )
            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except (ValueError, NetSapiensError, DigiCloudBillingProvisionError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/delete?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )

    notice = quote_plus(f"User {username} deleted successfully from DigiCloud")
    return RedirectResponse(
        f"/digicloud/users?domain={quote_plus(domain)}&notice={notice}",
        303,
    )


@router.get("/users/{username}/answering-rules", response_class=HTMLResponse)
async def live_digicloud_answering_rules(request: Request, username: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            if profile.get("hidden"):
                raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
            rules, raw_response = NetSapiensAnsweringRules().list(selected.domain_name, username)
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
        return render(
            request,
            "digicloud/user_management/answering_rules.html",
            selected_domain=selected,
            profile=profile,
            rules=rules,
            raw_response=raw_response,
            can_inspect=bool(user.is_superuser),
        )


@router.get("/users/{username}/answering-rules/edit", response_class=HTMLResponse)
async def edit_digicloud_answering_rule(request: Request, username: str, domain: str, timeframe: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            if profile.get("hidden"):
                raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
            rule = NetSapiensAnsweringRules().get(selected.domain_name, username, timeframe)
        except (NetSapiensError, ValueError) as exc:
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/answering-rules?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
        editor = NetSapiensAnsweringRules.editor_state(rule.get("raw", {}))
        editor["ring_seconds"] = profile.get("ring_seconds", "60")
        return render(request, "digicloud/user_management/answering_rule_edit.html",
                      selected_domain=selected, profile=profile, rule=rule, editor=editor)


@router.post("/users/{username}/answering-rules/edit")
async def save_digicloud_answering_rule(
    request: Request, username: str, domain: str = Form(...), timeframe: str = Form(...),
    enabled: str | None = Form(None),
    forward_always: str | None = Form(None), forward_always_destination: str = Form(""),
    forward_on_active: str | None = Form(None), forward_on_active_destination: str = Form(""),
    forward_busy: str | None = Form(None), forward_busy_destination: str = Form(""),
    forward_unanswered: str | None = Form(None), forward_unanswered_destination: str = Form(""),
    forward_offline: str | None = Form(None), forward_offline_destination: str = Form(""),
    simultaneous_enabled: str | None = Form(None),
    simultaneous_destinations: list[str] = Form(default=[]),
    ring_seconds: int = Form(60),
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        api = NetSapiensAnsweringRules()
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            if profile.get("hidden"):
                raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
            current = api.get(selected.domain_name, username, timeframe)

            forwards = {
                "always": {"enabled": bool_form(forward_always), "destination": forward_always_destination.strip()},
                "on_active": {"enabled": bool_form(forward_on_active), "destination": forward_on_active_destination.strip()},
                "busy": {"enabled": bool_form(forward_busy), "destination": forward_busy_destination.strip()},
                "unanswered": {"enabled": bool_form(forward_unanswered), "destination": forward_unanswered_destination.strip()},
                "offline": {"enabled": bool_form(forward_offline), "destination": forward_offline_destination.strip()},
            }
            for label, item in forwards.items():
                if item["enabled"] and not item["destination"]:
                    raise ValueError(f"A destination is required for enabled {label.replace('_', ' ')} forwarding")

            clean_destinations = []
            seen = set()
            for value in simultaneous_destinations:
                value = value.strip()
                if value and value not in seen:
                    clean_destinations.append(value)
                    seen.add(value)
            if ring_seconds < 5 or ring_seconds > 120 or ring_seconds % 5 != 0:
                raise ValueError("Ring duration must be between 5 and 120 seconds in 5-second increments")
            # Residential answering-rule editor intentionally exposes only
            # the supported routing controls. Advanced PBX options are fixed
            # to safe residential defaults and cannot be enabled from NOP.
            just_ring = False
            sim_enabled = bool_form(simultaneous_enabled)
            if forwards["always"]["enabled"] and sim_enabled:
                raise ValueError("Forward Always and Simultaneous Ring cannot both be enabled")
            if sim_enabled and not clean_destinations:
                raise ValueError("Simultaneous ring requires at least one destination")

            payload, provider_response = api.update(
                selected.domain_name, username, timeframe,
                enabled=bool_form(enabled), do_not_disturb=False,
                call_screening=False, forwards=forwards,
                simultaneous_enabled=sim_enabled, include_extension=False,
                ring_all_phones=False,
                answer_confirmation=False,
                simultaneous_destinations=clean_destinations,
                just_ring_extension=just_ring,
            )
            ring_provider_response = NetSapiensUsers().update_ring_timeout(
                selected.domain_name, username, ring_seconds
            )
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.answeringrule.update", "digicloud_answering_rule",
                f"{username}@{selected.domain_name}:{timeframe}",
                f"Updated answering rule {timeframe} for {username} in {selected.domain_name}",
                module="digicloud", organization_id=selected.organization_id,
                event_data={"before": current.get("raw", {}), "after": payload, "provider_response": provider_response, "ring_timeout_provider_response": ring_provider_response},
            )
            db.commit()
        except (NetSapiensError, ValueError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/answering-rules/edit?domain={quote_plus(selected.domain_name)}&timeframe={quote_plus(timeframe)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
    return RedirectResponse(
        f"/digicloud/users/{quote_plus(username)}/answering-rules?domain={quote_plus(domain)}&notice={quote_plus('Answering rule updated successfully')}", 303
    )


@router.post("/users/{username}/edit")
async def save_digicloud_user(
    request: Request,
    username: str,
    domain: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
    email: str = Form(""),
    department: str = Form(""),
    caller_id_name: str = Form(""),
    caller_id_number: str = Form(""),
    emergency_caller_id: str = Form(""),
    time_zone: str = Form(""),
    area_code: str = Form(""),
    enabled: str | None = Form(None),
    voicemail_enabled: str | None = Form(None),
    voicemail_notification_enabled: str | None = Form(None),
    voicemail_notification_email: str = Form(""),
    voicemail_email_type: str = Form("attachment"),
    voicemail_after_notification: str = Form("trash"),
):
    # Use the raw submitted form as the source of truth for checkbox and
    # dependent voicemail controls. Browser checkboxes are omitted entirely
    # when unchecked, and disabled controls are also omitted. Reading the raw
    # form prevents FastAPI defaults from accidentally converting a checked
    # voicemail notification switch into a provider-side "no" value.
    raw_form = await request.form()
    voicemail_enabled_value = raw_form.get("voicemail_enabled")
    voicemail_notification_enabled_value = raw_form.get("voicemail_notification_enabled")
    voicemail_notification_email_value = str(
        raw_form.get("voicemail_notification_email") or voicemail_notification_email or email
    ).strip()
    voicemail_email_type_value = str(
        raw_form.get("voicemail_email_type") or voicemail_email_type or "attachment"
    ).strip()
    voicemail_after_notification_value = str(
        raw_form.get("voicemail_after_notification") or voicemail_after_notification or "trash"
    ).strip()

    print(
        "DigiCloud voicemail form:",
        {
            "voicemail_enabled": voicemail_enabled_value,
            "voicemail_notification_enabled": voicemail_notification_enabled_value,
            "voicemail_notification_email": voicemail_notification_email_value,
            "voicemail_email_type": voicemail_email_type_value,
            "voicemail_after_notification": voicemail_after_notification_value,
        },
    )

    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        api = NetSapiensUsers()
        try:
            current = api.get(selected.domain_name, username)
            if current.get("hidden"):
                raise HTTPException(403, f"Protected DigiCloud user: {current.get('hidden_reason')}")
            submitted = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip(),
                "department": department.strip(),
                "caller_id_name": caller_id_name.strip(),
                "caller_id_number": caller_id_number.strip(),
                "emergency_caller_id": emergency_caller_id.strip(),
                "time_zone": time_zone.strip(),
                "language": "en_US",
                "area_code": area_code.strip(),
                "voicemail_enabled": bool_form(voicemail_enabled),
                "voicemail_notification_enabled": bool_form(voicemail_notification_enabled),
                "voicemail_notification_email": voicemail_notification_email.strip() or email.strip(),
                "voicemail_email_type": voicemail_email_type.strip(),
                "voicemail_after_notification": voicemail_after_notification.strip(),
                # Do not overwrite provider-specific states such as "pwd reset"
                # when DigiCloud did not normalize the current status to a boolean.
                "enabled": bool_form(enabled) if current.get("enabled") is not None else None,
            }
            api.update(selected.domain_name, username, submitted)
            voicemail_provider_response = api.update_voicemail_settings(
                selected.domain_name, username, submitted
            )

            # Re-read the live user so the redirect immediately reflects the
            # provider's saved voicemail notification values. If DigiCloud
            # silently ignores the request, report that instead of claiming a
            # successful update.
            refreshed = api.get(selected.domain_name, username)
            expected_notifications = {
                "enabled": submitted["voicemail_notification_enabled"],
                "recipient": submitted["voicemail_notification_email"] if submitted["voicemail_notification_enabled"] else "",
                "email_type": submitted["voicemail_email_type"],
                "after_action": submitted["voicemail_after_notification"],
            }
            actual_notifications = refreshed.get("voicemail_notifications", {})
            notification_mismatch = (
                bool(actual_notifications.get("enabled")) != bool(expected_notifications["enabled"])
                or (expected_notifications["enabled"] and str(actual_notifications.get("recipient") or "").strip().lower() != str(expected_notifications["recipient"] or "").strip().lower())
                or (expected_notifications["enabled"] and str(actual_notifications.get("email_type") or "") != str(expected_notifications["email_type"] or ""))
                or (expected_notifications["enabled"] and str(actual_notifications.get("after_action") or "") != str(expected_notifications["after_action"] or ""))
            )
            if notification_mismatch:
                raise NetSapiensError(
                    "DigiCloud did not retain the voicemail notification settings. "
                    f"Expected {expected_notifications}; received {actual_notifications}."
                )

            comparable_fields = (
                "first_name", "last_name", "email", "department",
                "caller_id_name", "caller_id_number", "emergency_caller_id",
                "time_zone", "language", "area_code", "enabled",
                "voicemail_enabled", "voicemail_notification_enabled",
                "voicemail_notification_email", "voicemail_email_type",
                "voicemail_after_notification",
            )
            changed_fields = {
                field: {"from": current.get(field), "to": submitted.get(field)}
                for field in comparable_fields
                if str(current.get(field, "")) != str(submitted.get(field, ""))
            }
            detail = (
                f"Updated DigiCloud user {username} in {selected.domain_name}; "
                f"changed {', '.join(changed_fields) if changed_fields else 'no profile fields'}"
            )
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.user.profile.update",
                "digicloud_user",
                f"{username}@{selected.domain_name}",
                detail,
                module="digicloud",
                organization_id=selected.organization_id,
                event_data={
                    "domain": selected.domain_name,
                    "username": username,
                    "changed_fields": changed_fields,
                },
            )
            db.commit()
        except HTTPException:
            raise
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/edit?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
    return RedirectResponse(
        f"/digicloud/users/{quote_plus(username)}/edit?domain={quote_plus(domain)}&notice=Profile+updated+in+DigiCloud",
        303,
    )



@router.get("/users/{username}/phones", response_class=HTMLResponse)
async def live_digicloud_phones(request: Request, username: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            if profile.get("hidden"):
                raise HTTPException(403, f"Protected DigiCloud user: {profile.get('hidden_reason')}")
            rows = NetSapiensDevices().list(selected.domain_name, username)
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/edit?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
        return render(
            request, "digicloud/user_management/phones.html",
            selected_domain=selected, profile=profile,
            devices=[_device_view(row) for row in rows],
        )


@router.get("/users/{username}/phones/new", response_class=HTMLResponse)
async def new_digicloud_phone(request: Request, username: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        profile = NetSapiensUsers().get(selected.domain_name, username)
        _, provisioning_server = _provisioning_context(db, selected.organization_id)
        server_options = _provisioning_servers()
        try:
            available_hardware = _available_inventory(
                NetSapiensPhoneProvisioning().list_domain_phones(selected.domain_name),
                selected.domain_name,
            )
        except NetSapiensError:
            available_hardware = []
        inventory_models = sorted({item["model"] for item in available_hardware if item["model"]}, key=str.casefold)
        return render(request, "digicloud/user_management/phone_add.html",
                      selected_domain=selected, profile=profile,
                      available_hardware=available_hardware, inventory_models=inventory_models,
                      provisioning_server=provisioning_server, server_options=server_options,
                      generated_sip_password=_generate_sip_password())


@router.post("/users/{username}/phones/new")
async def create_digicloud_phone(
    request: Request, username: str, domain: str = Form(...), setup_type: str = Form(...),
    inventory_mac: str = Form(""),
    sip_username: str = Form(""), sip_password: str = Form(""),
    preferred_server: str = Form(""), transport: str = Form("udp"),
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        _, configured_server = _provisioning_context(db, selected.organization_id)
        selected_server = preferred_server.strip() or configured_server
        try:
            before = NetSapiensDevices().list(selected.domain_name, username)
            if setup_type == "ata":
                normalized_mac = _normalize_mac(inventory_mac)
                if not normalized_mac:
                    raise ValueError("Select available phone hardware from this domain")
                inventory_rows = _available_inventory(
                    NetSapiensPhoneProvisioning().list_domain_phones(selected.domain_name),
                    selected.domain_name,
                )
                inventory = next((row for row in inventory_rows if row["mac"] == normalized_mac), None)
                if inventory is None:
                    raise ValueError("The selected phone is no longer available in this domain")
                selected_server = inventory["server"] or selected_server
                if not selected_server:
                    raise ValueError("The selected phone does not have a preferred server")
                provider_response = NetSapiensPhoneProvisioning().update_phone(
                    mac=inventory["mac"], model=inventory["model"], server=selected_server,
                    subscriber_name=username, domain=selected.domain_name,
                    transport=inventory["transport"], notes=inventory["notes"],
                    line_assignments=[f"sip:{username}@{selected.domain_name}"],
                )
                model = inventory["model"]
            elif setup_type == "manual":
                if not selected_server:
                    raise ValueError("No provisioning/core server is configured for this reseller")
                if not sip_password.strip():
                    raise ValueError("A SIP password is required for manual provisioning")
                provider_response = NetSapiensDevices().create_manual(selected.domain_name, username, {
                    "device": username,
                    "user": username,
                    "domain": selected.domain_name,
                    "login-username": (sip_username.strip() or f"{username}@{selected.domain_name}"),
                    "device-sip-registration-password": sip_password.strip(),
                    "device-sip-registration-core-server": selected_server,
                    "caller-id-number-emergency": "[*]",
                })
            else:
                raise ValueError("Choose Device Provisioning or Manual Provisioning")
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone.create", "digicloud_device", f"{username}@{selected.domain_name}",
                f"Added {setup_type} phone for {username} in {selected.domain_name}", module="digicloud",
                organization_id=selected.organization_id,
                event_data={"setup_type": setup_type, "model": model if setup_type == "ata" else "", "mac": _normalize_mac(inventory_mac) if setup_type == "ata" else "", "provider_response": provider_response, "before_count": len(before), "preferred_server": selected_server, "transport": transport, "emergency_caller_id": "[*]"},
            )
            db.commit()
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones/new?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
    return RedirectResponse(
        f"/digicloud/users/{quote_plus(username)}/phones?domain={quote_plus(domain)}&notice={quote_plus('Phone added to DigiCloud inventory and assigned to the user')}", 303
    )


@router.get("/users/{username}/phones/{device}/edit", response_class=HTMLResponse)
async def edit_digicloud_phone_page(request: Request, username: str, device: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            profile = NetSapiensUsers().get(selected.domain_name, username)
            row = NetSapiensDevices().get(selected.domain_name, username, device)
            if not row:
                raise HTTPException(404, "DigiCloud phone was not found")
            _, preferred_server = _provisioning_context(db, selected.organization_id)
            server_options = _provisioning_servers()
            domain_users = [item for item in NetSapiensUsers().list(selected.domain_name) if not item.get("hidden")]
            mac = _normalize_mac(str(row.get("device-provisioning-mac-address") or "")) if row.get("device-provisioning-mac-address") else ""
            model_details = {}
            if mac:
                try:
                    inventory = NetSapiensPhoneProvisioning().get_phone(mac)
                    if inventory:
                        row = {**row, **inventory}
                except NetSapiensError:
                    pass
                try:
                    model_display = str(row.get("device-models-brand-and-model") or row.get("device-models-model") or "")
                    brand, api_model = _model_identity(model_display)
                    if brand and api_model:
                        model_details = NetSapiensPhoneProvisioning().model_details(brand=brand, model=api_model)
                except NetSapiensError:
                    model_details = {}
            line_count = _model_line_count(model_details, row)
            line_assignments = []
            for index in range(1, line_count + 1):
                raw_line = row.get(f"device-provisioning-sip-uri-{index}") or ""
                line_assignments.append({"number": index, "value": _sip_uri_to_extension(raw_line)})
        except NetSapiensError as exc:
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
        return render(
            request, "digicloud/user_management/phone_edit.html",
            selected_domain=selected, profile=profile, phone=_device_view(row),
            preferred_server=preferred_server, server_options=server_options,
            domain_users=domain_users, line_assignments=line_assignments,
        )


@router.post("/users/{username}/phones/{device}/edit")
async def update_digicloud_phone(
    request: Request, username: str, device: str, domain: str = Form(...),
    preferred_server: str = Form(""), transport: str = Form("udp"),
    overrides: str = Form(""), sip_password: str = Form(""),
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            provider = NetSapiensDevices()
            before = provider.get(selected.domain_name, username, device)
            if not before:
                raise ValueError("DigiCloud phone was not found")
            is_provisioned = bool(before.get("device-models-model") or before.get("device-provisioning-mac-address"))
            if is_provisioned:
                raw_form = await request.form()
                raw_mac = str(before.get("device-provisioning-mac-address") or "")
                normalized_mac = _normalize_mac(raw_mac)
                server = preferred_server.strip()
                if not server:
                    _, server = _provisioning_context(db, selected.organization_id)
                if not server:
                    raise ValueError("A preferred provisioning server is required")
                line_fields = sorted(
                    (key for key in raw_form.keys() if str(key).startswith("line_")),
                    key=lambda key: int(str(key).split("_", 1)[1]),
                )
                line_assignments = [
                    _line_value_to_sip_uri(str(raw_form.get(key) or ""), selected.domain_name)
                    for key in line_fields
                ]
                primary_subscriber = next((value for value in line_assignments if value), "")
                provider_response = NetSapiensPhoneProvisioning().update_phone(
                    mac=normalized_mac,
                    server=server,
                    domain=selected.domain_name,
                    subscriber_name=_sip_uri_to_extension(primary_subscriber),
                    transport=transport,
                    notes=overrides,
                    line_assignments=line_assignments,
                )
            else:
                payload = {"caller-id-number-emergency": "[*]"}
                server = preferred_server.strip()
                if server:
                    payload["device-sip-registration-core-server"] = server
                if sip_password.strip():
                    payload["device-sip-registration-password"] = sip_password.strip()
                provider_response = provider.update(selected.domain_name, username, device, payload)
            after = provider.get(selected.domain_name, username, device)
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone.update", "digicloud_device", f"{device}@{selected.domain_name}",
                f"Updated phone {device} for {username}", module="digicloud",
                organization_id=selected.organization_id,
                event_data={"domain": selected.domain_name, "username": username, "device": device,
                            "before": {k:v for k,v in before.items() if "password" not in k.lower()},
                            "after": {k:v for k,v in after.items() if "password" not in k.lower()},
                            "provider_response": provider_response},
            )
            db.commit()
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones/{quote_plus(device)}/edit?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
    return RedirectResponse(
        f"/digicloud/users/{quote_plus(username)}/phones?domain={quote_plus(domain)}&notice={quote_plus('Phone updated successfully')}", 303
    )


@router.post("/users/{username}/phones/{device}/reset-password", response_class=HTMLResponse)
async def reset_manual_digicloud_phone_password(
    request: Request,
    username: str,
    device: str,
    domain: str = Form(...),
    return_to: str = Form(""),
):
    """Replace a manual SIP password and expose the replacement once."""
    user = require_user_management_access(request)
    safe_return = return_to if return_to.startswith("/customers/") else ""
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        try:
            provider = NetSapiensDevices()
            before = provider.get(selected.domain_name, username, device)
            if not before:
                raise ValueError("DigiCloud phone was not found")
            if before.get("device-models-model") or before.get("device-provisioning-mac-address"):
                raise ValueError("SIP password reset is available only for manually provisioned devices.")
            new_password = _generate_sip_password()
            server = str(
                before.get("core-server")
                or before.get("device-sip-registration-core-server")
                or before.get("device-provisioning-registration-core-server")
                or ""
            ).strip()
            if not server:
                _, server = _provisioning_context(db, selected.organization_id)
            provider.update(
                selected.domain_name,
                username,
                device,
                {
                    "device-sip-registration-password": new_password,
                    "caller-id-number-emergency": "[*]",
                    **({"device-sip-registration-core-server": server} if server else {}),
                },
            )
            login = str(
                before.get("login-username")
                or before.get("device-sip-registration-uri")
                or f"{username}@{selected.domain_name}"
            ).removeprefix("sip:")
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone.password_reset",
                "digicloud_device",
                f"{device}@{selected.domain_name}",
                f"Reset the one-time SIP password for manual device {device}",
                module="digicloud",
                organization_id=selected.organization_id,
                event_data={
                    "domain": selected.domain_name,
                    "username": username,
                    "device": device,
                    "password_stored": False,
                },
            )
            db.commit()
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones/{quote_plus(device)}/edit"
                f"?domain={quote_plus(selected.domain_name)}"
                f"&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}",
                303,
            )
        return render(
            request,
            "digicloud/user_management/sip_password_reset.html",
            selected_domain=selected,
            username=username,
            device=device,
            sip_username=login,
            sip_password=new_password,
            provisioning_server=server,
            return_to=safe_return,
        )


@router.get("/users/{username}/phones/{device}/delete", response_class=HTMLResponse)
async def delete_digicloud_phone_page(request: Request, username: str, device: str, domain: str):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        profile = NetSapiensUsers().get(selected.domain_name, username)
        row = NetSapiensDevices().get(selected.domain_name, username, device)
        if not row:
            raise HTTPException(404, "DigiCloud phone was not found")
        return render(request, "digicloud/user_management/phone_delete.html",
                      selected_domain=selected, profile=profile, phone=_device_view(row))


@router.post("/users/{username}/phones/{device}/delete")
async def delete_digicloud_phone(
    request: Request, username: str, device: str, domain: str = Form(...),
    confirmation: str = Form(""),
    delete_confirmation: str = Form(""),
):
    user = require_user_management_access(request)
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)
        confirmation_value = (confirmation or delete_confirmation).strip()
        if confirmation_value not in {device, "delete"}:
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones/{quote_plus(device)}/delete?domain={quote_plus(selected.domain_name)}&error={quote_plus('Type the exact device name or delete to confirm deletion')}", 303
            )
        try:
            provider = NetSapiensDevices()
            before = provider.get(selected.domain_name, username, device)
            raw_mac = str(before.get("device-provisioning-mac-address") or "").strip()
            provisioning = NetSapiensPhoneProvisioning()

            # Some DigiCloud device responses omit the provisioning MAC even
            # though the record came from the MAC inventory. Resolve it from
            # /phones by domain/subscriber before deciding this is manual SIP.
            if not raw_mac:
                target_domain = selected.domain_name.casefold()
                target_user = username.casefold()
                target_device = str(device or "").strip().casefold()
                inventory_matches = []
                for phone_row in provisioning.list_phones():
                    if not isinstance(phone_row, dict):
                        continue
                    phone_domain = str(
                        phone_row.get("domain")
                        or phone_row.get("device-domain")
                        or phone_row.get("device-provisioning-domain")
                        or ""
                    ).strip().casefold()
                    subscriber = str(
                        phone_row.get("subscriber_name")
                        or phone_row.get("subscriber-name")
                        or phone_row.get("subscriber")
                        or phone_row.get("user")
                        or phone_row.get("device-provisioning-subscriber-name")
                        or ""
                    ).strip().casefold()
                    if phone_domain != target_domain or subscriber != target_user:
                        continue
                    inventory_matches.append(phone_row)

                # Prefer a row whose configured model matches the device label.
                # Production /phones responses vary widely in field names, so
                # compare every known model/display field and also tolerate the
                # short API model value (for example ``801`` vs
                # ``Grandstream 801``).
                selected_inventory = None
                for phone_row in inventory_matches:
                    model_values = {
                        str(phone_row.get(key) or "").strip().casefold()
                        for key in (
                            "device-models-brand-and-model", "brand_model",
                            "model", "device-models-model",
                            "device-provisioning-model", "phone-model",
                        )
                        if str(phone_row.get(key) or "").strip()
                    }
                    if target_device and any(
                        target_device == value
                        or target_device.endswith(" " + value)
                        or value.endswith(" " + target_device)
                        for value in model_values
                    ):
                        selected_inventory = phone_row
                        break

                # A residential user commonly has a single provisioned MAC. If
                # so, that row is unambiguous even when the API omits model
                # metadata. Never fall through to the unsupported user-device
                # DELETE route merely because the collection response omitted
                # its MAC/model fields.
                if selected_inventory is None and len(inventory_matches) == 1:
                    selected_inventory = inventory_matches[0]

                if selected_inventory is not None:
                    raw_mac = str(
                        selected_inventory.get("device-provisioning-mac-address")
                        or selected_inventory.get("mac")
                        or selected_inventory.get("mac-address")
                        or selected_inventory.get("phone-mac")
                        or ""
                    ).strip()

            if raw_mac:
                normalized_mac = _normalize_mac(raw_mac)
                # Removing the MAC inventory record also removes its DigiCloud
                # user assignment. Do not call the device DELETE route after
                # this; some deployed builds return No Route Found [92] for
                # provisioned device names containing spaces.
                provider_response = provisioning.delete_phone(normalized_mac)
            else:
                # Manual provisioning records use the subscriber/extension as
                # the device name. A model-like device label indicates a
                # provisioned phone whose MAC could not be resolved; do not call
                # the unsupported device-specific DELETE route because this
                # NetSapiens deployment returns No Route Found [92].
                if str(device or "").strip().casefold() != str(username or "").strip().casefold():
                    raise ValueError(
                        "Unable to locate this provisioned phone in DigiCloud phone inventory. "
                        "Refresh the phone inventory and verify the MAC is assigned to this user."
                    )
                provider_response = provider.delete(selected.domain_name, username, device)
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone.delete", "digicloud_device", f"{device}@{selected.domain_name}",
                f"Deleted phone {device} from {username}", module="digicloud",
                organization_id=selected.organization_id,
                event_data={"domain": selected.domain_name, "username": username, "device": device,
                            "deleted": {k:v for k,v in before.items() if "password" not in k.lower()},
                            "provider_response": provider_response},
            )
            db.commit()
        except (ValueError, NetSapiensError) as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones?domain={quote_plus(selected.domain_name)}&error={quote_plus(str(exc).replace('NetSapiens', 'DigiCloud'))}", 303
            )
        except Exception as exc:
            db.rollback()
            return RedirectResponse(
                f"/digicloud/users/{quote_plus(username)}/phones?domain={quote_plus(selected.domain_name)}&error={quote_plus('Unable to delete phone: ' + str(exc))}", 303
            )
    return RedirectResponse(
        f"/digicloud/users/{quote_plus(username)}/phones?domain={quote_plus(domain)}&notice={quote_plus('Phone deleted successfully')}", 303
    )


@router.get("/phone-hardware", response_class=HTMLResponse)
async def digicloud_phone_hardware(
    request: Request,
    organization_id: int | None = None,
    domain: str = "",
    brand: str = "",
    model: str = "",
    status: str = "all",
    mac: str = "",
):
    """Show reseller-scoped DigiCloud phone hardware with inventory filters.

    Reseller users are restricted to hardware whose domain is assigned to their
    own NOP organization. Unassigned/global inventory rows are intentionally
    hidden from reseller users because they cannot be attributed safely. NOP
    superusers may select an organization/reseller explicitly.
    """
    require_permission(request, "digicloud.hardware.read")
    user = require_user_management_access(request)
    with SessionLocal() as db:
        organizations = admin_organizations(db) if user.is_superuser else []
        if user.is_superuser:
            all_domains = allowed_user_domains(db, user)
            selected_org_id = organization_id
            if selected_org_id is None and domain:
                match = next((item for item in all_domains if item.domain_name.casefold() == domain.casefold()), None)
                selected_org_id = match.organization_id if match else None
            linked_org_ids = {item.organization_id for item in all_domains}
            if selected_org_id is None:
                selected_org_id = next((org.id for org in organizations if org.id in linked_org_ids), None)
            domains = [item for item in all_domains if item.organization_id == selected_org_id] if selected_org_id is not None else []
        else:
            selected_org_id = user.organization_id
            domains = allowed_user_domains(db, user)

        allowed_domain_names = {item.domain_name.casefold() for item in domains}
        if domain and domain.casefold() not in allowed_domain_names:
            raise HTTPException(403, "This DigiCloud domain is not owned by the selected reseller.")

        try:
            rows = [_phone_inventory_view(row) for row in NetSapiensPhoneProvisioning().list_phones()]
        except NetSapiensError as exc:
            rows = []
            live_error = str(exc).replace("NetSapiens", "DigiCloud")
        else:
            live_error = ""

        # Inventory ownership is established by its assigned DigiCloud domain.
        # Do not expose blank-domain inventory to reseller users. Platform admins
        # see only the domains belonging to the reseller/organization they chose.
        rows = [row for row in rows if row["domain"].casefold() in allowed_domain_names]

        catalog = _device_catalog()
        catalog_by_display = {item["brand_model"].casefold(): item for item in catalog}
        catalog_by_api = {item["model"].casefold(): item for item in catalog if item["model"]}
        for row in rows:
            source = catalog_by_display.get(row["model"].casefold()) or catalog_by_api.get(row["model"].casefold())
            row["brand"] = (source["brand"] if source else _model_identity(row["model"])[0]) or "Unknown"

        all_brands = sorted({row["brand"] for row in rows}, key=str.casefold)
        models_for_brand = sorted(
            {row["model"] for row in rows if not brand or row["brand"].casefold() == brand.casefold()},
            key=str.casefold,
        )

        if domain:
            rows = [row for row in rows if row["domain"].casefold() == domain.casefold()]
        if brand:
            rows = [row for row in rows if row["brand"].casefold() == brand.casefold()]
        if model:
            rows = [row for row in rows if row["model"].casefold() == model.casefold()]
        if status == "available":
            rows = [row for row in rows if not row["assigned"]]
        elif status == "assigned":
            rows = [row for row in rows if row["assigned"]]

        mac_filter = re.sub(r"[^0-9A-Fa-f]", "", mac or "").upper()
        if mac_filter:
            rows = [
                row for row in rows
                if mac_filter in re.sub(r"[^0-9A-Fa-f]", "", row.get("mac") or "").upper()
            ]

        rows.sort(key=lambda row: (row["brand"].casefold(), row["model"].casefold(), row["mac"]))
        return render(
            request, "digicloud/phone_hardware.html",
            rows=rows, domains=domains, organizations=organizations,
            selected_organization_id=selected_org_id, selected_domain=domain,
            brands=all_brands, models=models_for_brand, selected_brand=brand,
            selected_model=model, selected_status=status, selected_mac=mac, live_error=live_error,
            is_platform_admin=user.is_superuser,
        )


@router.get("/phone-hardware/new", response_class=HTMLResponse)
async def new_digicloud_phone_hardware(request: Request, domain: str = ""):
    require_permission(request, "digicloud.hardware.manage")
    user = require_user_management_access(request)
    with SessionLocal() as db:
        domains = allowed_user_domains(db, user)
        selected = next((item for item in domains if item.domain_name == domain), domains[0] if domains else None)
        if selected is None:
            raise HTTPException(404, "No DigiCloud user-management domain is configured.")
        _, server = _provisioning_context(db, selected.organization_id)
        try:
            live_inventory = NetSapiensPhoneProvisioning().list_domain_phones(selected.domain_name)
            models = sorted(
                {view["model"] for view in map(_phone_inventory_view, live_inventory) if view["model"]},
                key=str.casefold,
            )
        except NetSapiensError:
            models = []
        return render(request, "digicloud/phone_hardware_add.html", selected_domain=selected,
                      domains=domains, models=models, preferred_server=server, servers=_provisioning_servers())


@router.post("/phone-hardware/new")
async def create_digicloud_phone_hardware(
    request: Request, domain: str = Form(...), model_name: str = Form(...),
    mac: str = Form(...), server: str = Form(""), transport: str = Form("udp"),
    notes: str = Form(""),
):
    require_permission(request, "digicloud.hardware.manage")
    with SessionLocal() as db:
        user = require_user_management_access(request)
        selected = require_allowed_domain(db, user, domain)
        _, default_server = _provisioning_context(db, selected.organization_id)
        model_name = model_name.strip()
        if not model_name:
            return RedirectResponse(f"/digicloud/phone-hardware/new?domain={quote_plus(domain)}&error=Enter+a+DigiCloud+model", 303)
        normalized_mac = _normalize_mac(mac)
        if len(normalized_mac) != 12:
            return RedirectResponse(f"/digicloud/phone-hardware/new?domain={quote_plus(domain)}&error=Enter+a+valid+12-character+MAC+address", 303)
        target_server = server.strip() or default_server
        if not target_server:
            return RedirectResponse(f"/digicloud/phone-hardware/new?domain={quote_plus(domain)}&error=Configure+a+preferred+server+for+this+reseller", 303)
        try:
            response = NetSapiensPhoneProvisioning().provision(
                mac=normalized_mac, model=model_name,
                server=target_server, domain=selected.domain_name, subscriber_name="",
                transport=transport, notes=notes.strip(),
            )
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone_inventory.create", "digicloud_phone_inventory", normalized_mac,
                f"Added {model_name} ({normalized_mac}) to DigiCloud phone inventory",
                module="digicloud", organization_id=selected.organization_id,
                event_data={"domain": selected.domain_name, "model": model_name,
                            "server": target_server, "transport": transport, "provider_response": response},
            )
            db.commit()
        except NetSapiensError as exc:
            db.rollback()
            return RedirectResponse(f"/digicloud/phone-hardware/new?domain={quote_plus(domain)}&error={quote_plus(str(exc).replace('NetSapiens','DigiCloud'))}",303)
    return RedirectResponse(f"/digicloud/phone-hardware?domain={quote_plus(domain)}&notice=Phone+added+to+DigiCloud+inventory",303)


@router.get("/phone-hardware/{mac}/edit", response_class=HTMLResponse)
async def edit_digicloud_phone_hardware_page(request: Request, mac: str, organization_id: int | None = None):
    require_permission(request, "digicloud.hardware.manage")
    with SessionLocal() as db:
        user, organizations, selected_org_id, domains, item = _require_hardware_access(request, db, mac, organization_id)
        raw_item = item["raw"]
        assigned_indexes = [
            index for index in range(1, 9)
            if _sip_uri_to_extension(raw_item.get(f"device{index}") or raw_item.get(f"device-provisioning-sip-uri-{index}") or "")
        ]
        line_count = max(assigned_indexes, default=1)
        line_values = []
        for index in range(1, line_count + 1):
            raw = item["raw"]
            value = raw.get(f"device-provisioning-sip-uri-{index}") or raw.get(f"device{index}") or ""
            line_values.append(_sip_uri_to_extension(value))
        users = ([user_row for user_row in NetSapiensUsers().list(item["domain"]) if not user_row.get("hidden")]
                 if item["domain"] else [])
        return render(request, "digicloud/phone_hardware_edit.html", item=item, domains=domains, users=users,
                      line_values=line_values, line_count=line_count, servers=_default_provisioning_servers(),
                      selected_organization_id=selected_org_id, is_platform_admin=user.is_superuser)

@router.post("/phone-hardware/{mac}/edit")
async def update_digicloud_phone_hardware(request: Request, mac: str, organization_id: int | None = None):
    require_permission(request, "digicloud.hardware.manage")
    form = await request.form()
    with SessionLocal() as db:
        user, organizations, selected_org_id, domains, item = _require_hardware_access(request, db, mac, organization_id)
        server = str(form.get("server") or item["server"]).strip()
        transport = str(form.get("transport") or item["transport"] or "udp").lower()
        notes = str(form.get("notes") or "").strip()
        overrides = str(form.get("overrides") or "").strip()
        line_count = max(1, min(int(form.get("line_count") or 1), 8))
        lines = [_line_value_to_sip_uri(str(form.get(f"line_{i}") or ""), item["domain"]) for i in range(1, line_count + 1)]
        subscriber = _sip_uri_to_extension(lines[0]) if lines and lines[0] else ""
        try:
            provider = NetSapiensPhoneProvisioning()
            response = provider.update_phone(
                mac=item["mac"], model=item["model"], server=server, domain=item["domain"],
                subscriber_name=subscriber, transport=transport, notes=notes,
                overrides=overrides, line_assignments=lines,
            )
            refreshed = _find_phone_inventory(item["mac"])
            if not refreshed:
                raise NetSapiensError(502, "DigiCloud accepted the update but the phone could not be reloaded from inventory.")
            # Compare normalized extension assignments rather than provider display
            # strings. DigiCloud commonly returns "n/a" for a blank line while NOP
            # submits an empty value. Both represent the same unassigned state.
            expected_lines = [_sip_uri_to_extension(value) for value in lines]
            actual_lines = []
            raw_refreshed = refreshed.get("raw") or {}
            for index in range(1, line_count + 1):
                actual_value = (
                    raw_refreshed.get(f"device{index}")
                    or raw_refreshed.get(f"device-provisioning-sip-uri-{index}")
                    or ""
                )
                actual_lines.append(_sip_uri_to_extension(actual_value))
            if (str(refreshed.get("server") or "").strip().casefold() != server.casefold()
                    or str(refreshed.get("transport") or "udp").strip().casefold() != transport.casefold()
                    or actual_lines != expected_lines):
                raise NetSapiensError(
                    502,
                    "DigiCloud did not retain one or more phone hardware changes. "
                    f"Expected server={server!r}, transport={transport!r}, lines={expected_lines!r}; "
                    f"received server={refreshed.get('server')!r}, transport={refreshed.get('transport')!r}, lines={actual_lines!r}."
                )
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone_inventory.update", "digicloud_phone_inventory", item["mac"],
                f"Updated {item['model']} ({item['mac']}) in DigiCloud phone inventory",
                module="digicloud", organization_id=selected_org_id,
                event_data={"domain": item["domain"], "server": server, "transport": transport,
                            "line_assignments": lines, "overrides": overrides, "provider_response": response},
            )
            db.commit()
        except NetSapiensError as exc:
            db.rollback()
            return RedirectResponse(f"/digicloud/phone-hardware/{quote_plus(item['mac'])}/edit?organization_id={selected_org_id or ''}&error={quote_plus(str(exc).replace('NetSapiens','DigiCloud'))}",303)
    return RedirectResponse(f"/digicloud/phone-hardware?organization_id={selected_org_id or ''}&notice=Phone+hardware+updated",303)

@router.get("/phone-hardware/{mac}/delete", response_class=HTMLResponse)
async def delete_digicloud_phone_hardware_page(request: Request, mac: str, organization_id: int | None = None):
    require_permission(request, "digicloud.hardware.manage")
    with SessionLocal() as db:
        user, organizations, selected_org_id, domains, item = _require_hardware_access(request, db, mac, organization_id)
        return render(request, "digicloud/phone_hardware_delete.html", item=item, selected_organization_id=selected_org_id)

@router.post("/phone-hardware/{mac}/delete")
async def delete_digicloud_phone_hardware(request: Request, mac: str, organization_id: int | None = None, confirmation: str = Form(...)):
    require_permission(request, "digicloud.hardware.manage")
    with SessionLocal() as db:
        user, organizations, selected_org_id, domains, item = _require_hardware_access(request, db, mac, organization_id)
        if confirmation.strip().casefold() != "delete":
            return RedirectResponse(f"/digicloud/phone-hardware/{quote_plus(item['mac'])}/delete?organization_id={selected_org_id or ''}&error=Type+delete+to+confirm",303)
        if item["assigned"]:
            return RedirectResponse(f"/digicloud/phone-hardware/{quote_plus(item['mac'])}/delete?organization_id={selected_org_id or ''}&error=Unassign+this+hardware+before+deleting+it",303)
        try:
            response = NetSapiensPhoneProvisioning().delete_phone(item["mac"])
            AuditService(db, request, context_from_request(request)).record(
                "digicloud.phone_inventory.delete", "digicloud_phone_inventory", item["mac"],
                f"Deleted {item['model']} ({item['mac']}) from DigiCloud phone inventory",
                module="digicloud", organization_id=selected_org_id,
                event_data={"domain": item["domain"], "model": item["model"], "provider_response": response},
            )
            db.commit()
        except NetSapiensError as exc:
            db.rollback()
            return RedirectResponse(f"/digicloud/phone-hardware/{quote_plus(item['mac'])}/delete?organization_id={selected_org_id or ''}&error={quote_plus(str(exc).replace('NetSapiens','DigiCloud'))}",303)
    return RedirectResponse(f"/digicloud/phone-hardware?organization_id={selected_org_id or ''}&notice=Phone+hardware+deleted",303)


@router.get("/admin/device-models", response_class=HTMLResponse)
async def legacy_digicloud_device_models(request: Request):
    require_permission(request, "digicloud.settings")
    return RedirectResponse(
        "/digicloud/phone-hardware?notice=Provisioning+Devices+was+retired.+Use+live+Phone+Hardware+inventory.",
        303,
    )

@router.post("/admin/device-models")
async def legacy_save_digicloud_device_models(request: Request):
    require_permission(request, "digicloud.settings")
    return RedirectResponse(
        "/digicloud/phone-hardware?notice=Provisioning+Devices+was+retired.+Use+live+Phone+Hardware+inventory.",
        303,
    )

@router.get("/admin/api-inspector/user", response_class=HTMLResponse)
async def digicloud_user_api_inspector(
    request: Request,
    domain: str,
    username: str,
):
    user = require_user_management_access(request)
    if not user.is_superuser:
        raise HTTPException(403, "NOP superuser access is required.")
    with SessionLocal() as db:
        selected = require_allowed_domain(db, user, domain)

    client = NetSapiensClient()
    encoded_domain = quote_plus(selected.domain_name)
    encoded_username = quote_plus(username)
    detail = client.inspect(
        "GET",
        f"/domains/{encoded_domain}/users/{encoded_username}",
    )
    collection = client.inspect(
        "GET",
        f"/domains/{encoded_domain}/users",
        params={"limit": 10000},
    )
    return render(
        request,
        "digicloud/user_management/api_inspector.html",
        selected_domain=selected,
        username=username,
        detail=detail,
        collection=collection,
    )


@router.get("/admin/user-domains")
async def user_domain_access_admin(request: Request):
    require_platform_staff(request)
    return RedirectResponse("/organizations?notice=Domain+access+is+now+derived+from+the+linked+DigiCloud+reseller", 303)
