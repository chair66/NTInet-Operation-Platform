from __future__ import annotations

import re
from typing import Any

from app.services.platypus import PlatypusAPIError, PlatypusClient


DIGICLOUD_RESIDENTIAL_RATES = {
    "249": "DigiCloud Residential",
    "98": "DigiCloud Residential",
    "99": "DigiCloud Residential",
}
class DigiCloudBillingProvisionError(RuntimeError):
    def __init__(self, message: str, *, crid: str = "") -> None:
        super().__init__(message)
        self.crid = crid


def normalize_mac(value: str, *, required: bool = True) -> str:
    normalized = re.sub(r"[^0-9A-Fa-f]", "", value or "").upper()
    if not normalized and not required:
        return ""
    if len(normalized) != 12:
        raise ValueError("Phone MAC address must contain exactly 12 hexadecimal characters.")
    return normalized


def _key(row: dict[str, Any]) -> str:
    return re.sub(r"[^a-z0-9]", "", f"{row.get('datahdr', '')} {row.get('datacol', '')}".lower())


def _field_value(row: dict[str, Any], values: dict[str, str]) -> str:
    key = _key(row)
    mappings: tuple[tuple[tuple[str, ...], str], ...] = (
        (("linenumber",), "line_number"),
        (("phonenumber", "telephone", "tnnumber"), "phone_number"),
        (("macaddress", "phonemac", "devicemac"), "mac_address"),
        (("pincode", "vmpass", "voicemailpassword", "voicemailpin"), "voicemail_pin"),
        (("ringsbeforevmail", "ringsbeforevoicemail"), "rings_before_vmail"),
        (("voicemailprovisioned",), "voicemail_provisioned"),
        (("voicemailenabled",), "voicemail_enabled"),
        (("voicemailtoemailtype", "voicemailemailtype"), "voicemail_email_type"),
        (("emailaddress",), "email_address"),
        (("holddialplan",), "hold_dial_plan"),
        (("defaultdialplan",), "default_dial_plan"),
        (("dialplan",), "dial_plan"),
        (("domain",), "domain"),
        (("reseller",), "reseller"),
        (("holdapplication",), "hold_application"),
        (("defaultapplication",), "default_application"),
        (("application",), "application"),
        (("dndenabled",), "disabled_flag"),
        (("forwardalwaysnumber", "forwardnoanswernumber", "forwardnotregisterednumber", "forwardbusynumber"), "blank"),
        (("forwardalwaysenable", "forwardnoanswerenable", "forwardnotregistered", "forwardbusyenable", "screenanon", "screenanonymous"), "disabled_flag"),
        (("overrides",), "blank"),
    )
    for needles, value_key in mappings:
        if any(needle in key for needle in needles):
            return values[value_key]
    default = str(row.get("template_dflt") or row.get("dflt") or "").strip()
    return "" if default.upper() == "NULL" else default


def build_service_fields(rows: list[dict[str, Any]], values: dict[str, str]) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    missing: list[str] = []
    for row in rows:
        column = str(row.get("datacol") or "").strip()
        if not column or str(row.get("readonly") or "N").upper() == "Y":
            continue
        key = _key(row)
        value = _field_value(row, values)
        # Manual SIP provisioning has no physical phone MAC. The Digital Phone
        # definition may advertise the legacy MAC field as required even though
        # its API accepts an empty value for a manually provisioned subscriber.
        optional_manual_mac = not values.get("mac_address") and any(
            token in key for token in ("macaddress", "phonemac", "devicemac")
        )
        if str(row.get("reqd") or "N").upper() == "Y" and not value and not optional_manual_mac:
            missing.append(str(row.get("datahdr") or column))
        fields.append({
            "column_name": column,
            "newvalue": value,
            "oldvalue": "",
            "control": str(row.get("ctrl") or "txt_text"),
            "display": str(row.get("datahdr") or column),
        })
    if missing:
        raise ValueError("Required DigiCloud billing fields could not be populated: " + ", ".join(missing))
    if not fields:
        raise ValueError("Platypus returned no writable fields for the Digital Phone service.")
    return fields


def _has_writable_fields(rows: list[dict[str, Any]]) -> bool:
    return any(
        str(row.get("datacol") or "").strip()
        and str(row.get("readonly") or "N").upper() != "Y"
        for row in rows
    )


async def _service_definition_for_rate(
    client: PlatypusClient,
    *,
    customer_id: str,
    rate_group_id: str,
    crid: str,
) -> tuple[str, list[dict[str, Any]], str]:
    """Resolve only the Digital Phone definition attached to one assigned rate."""
    digital_phone_ids: list[str] = []
    available_services: list[str] = []
    try:
        for row in await client.list_service_tree(customer_id):
            row_crid = str(
                row.get("rs_cr_id") or row.get("crid") or row.get("cr_id") or row.get("s_custrate") or ""
            ).strip()
            if row_crid != crid:
                continue
            service_id = str(
                row.get("rs_svc_id") or row.get("svc_id") or row.get("s_svc_id") or row.get("serviceid") or ""
            ).strip()
            service_name = str(
                row.get("rs_path") or row.get("rs_name") or row.get("s_name")
                or row.get("service_name") or row.get("name") or ""
            ).strip()
            if service_id:
                available_services.append(f"{service_name or 'Unnamed'} (SVC {service_id})")
            normalized_name = re.sub(r"[^a-z0-9]", "", service_name.lower())
            if service_id and "digitalphone" in normalized_name and service_id not in digital_phone_ids:
                digital_phone_ids.append(service_id)
    except PlatypusAPIError as exc:
        raise ValueError(
            "NOP could not read the assigned rate's service tree to locate Digital Phone: "
            f"{exc}"
        ) from exc
    if not digital_phone_ids:
        available_note = ", ".join(available_services) if available_services else "none returned"
        raise ValueError(
            f"CRID {crid} does not expose a Digital Phone service definition. "
            f"Available services: {available_note}."
        )
    if len(digital_phone_ids) > 1:
        raise ValueError(
            f"CRID {crid} exposes multiple Digital Phone service IDs: "
            + ", ".join(digital_phone_ids)
        )

    diagnostics: list[str] = []
    for service_id in digital_phone_ids:
        # Platypus documents that a valid RGID causes CRID to be ignored. Use
        # mutually exclusive scopes, starting with the assigned-rate CRID.
        attempts = (
            ("assigned rate", 0, crid),
            ("rate template", rate_group_id, 0),
            ("service defaults", 0, 0),
        )
        for label, rgid_value, crid_value in attempts:
            try:
                rows = await client.get_service_info(
                    service_id, rgid=rgid_value, crid=crid_value
                )
            except PlatypusAPIError as exc:
                if exc.code != "DATA_ERROR":
                    raise
                diagnostics.append(f"SVC {service_id} {label}: {exc.code}")
                continue
            writable = sum(
                1 for row in rows
                if str(row.get("datacol") or "").strip()
                and str(row.get("readonly") or "N").upper() != "Y"
            )
            diagnostics.append(f"SVC {service_id} {label}: {len(rows)} rows/{writable} writable")
            if _has_writable_fields(rows):
                return service_id, rows, label
    raise ValueError(
        "Platypus returned no writable fields for the Digital Phone service attached "
        f"to CRID {crid}. " + "; ".join(diagnostics)
    )


def _service_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    service_name = str(
        row.get("s_name") or row.get("rs_path") or row.get("service_name") or row.get("name") or ""
    ).strip()
    service_type_id = str(
        row.get("s_svc_id") or row.get("rs_svc_id") or row.get("svc_id") or row.get("serviceid") or ""
    ).strip()
    data_id = str(
        row.get("s_num") or row.get("data_id") or row.get("dataid") or row.get("instance") or ""
    ).strip()
    return service_name, service_type_id, data_id


def _is_ata_service(row: dict[str, Any]) -> bool:
    service_name, _, _ = _service_identity(row)
    return bool(re.search(r"(^|[^a-z])ata([^a-z]|$)", service_name.lower()))


async def provision_residential_billing(
    client: PlatypusClient,
    *,
    customer_id: str,
    rate_group_id: str,
    phone_number: str,
    mac_address: str,
    voicemail_pin: str,
    voicemail_enabled: bool,
    voicemail_email_enabled: bool,
    email_address: str,
    domain: str,
    reseller_name: str = "NTInet",
    allowed_rate_group_ids: set[str] | None = None,
    existing_crid: str = "",
) -> dict[str, Any]:
    permitted_rates = allowed_rate_group_ids or set(DIGICLOUD_RESIDENTIAL_RATES)
    if rate_group_id not in permitted_rates:
        raise ValueError("Select a supported DigiCloud billing rate.")
    mac = normalize_mac(mac_address, required=False)
    values = {
        "line_number": "1",
        "phone_number": phone_number,
        "mac_address": mac,
        "voicemail_pin": voicemail_pin,
        "rings_before_vmail": "20",
        "voicemail_provisioned": "1" if voicemail_enabled else "0",
        "voicemail_enabled": "1" if voicemail_enabled else "0",
        "voicemail_email_type": "1" if voicemail_email_enabled else "0",
        "email_address": email_address,
        "domain": domain,
        "reseller": reseller_name.strip() or "NTInet",
        "application": "To User Residential",
        "dial_plan": domain,
        "hold_application": "Hangup",
        "default_application": "To User Residential",
        "hold_dial_plan": "Customer On Hold",
        "default_dial_plan": domain,
        "disabled_flag": "0",
        "blank": "",
    }
    # Create the customer rate first, then locate the Digital Phone service in
    # that assigned rate's live service tree. Reuse one incomplete/ATA-only
    # rate on retry so repair cannot duplicate monthly billing.
    try:
        rates = await client.get_rates(customer_id)
    except PlatypusAPIError as exc:
        if exc.code == "DATA_ERROR" or "No Rate Groups have been assigned" in exc.message:
            rates = []
        else:
            raise
    repairable_crids: list[str] = []
    for rate in rates:
        existing_rgid = str(rate.get("rgid") or rate.get("rg_id") or rate.get("cr_rg_id") or "").strip()
        rate_crid = str(rate.get("crid") or rate.get("cr_id") or rate.get("cr_crid") or "").strip()
        if existing_rgid != rate_group_id or not rate_crid:
            continue
        try:
            services = await client.list_services2(customer_id, crid=rate_crid)
        except PlatypusAPIError as exc:
            if exc.code == "DATA_ERROR":
                services = []
            else:
                raise
        if not services or all(_is_ata_service(service) for service in services):
            repairable_crids.append(rate_crid)
    requested_crid = str(existing_crid or "").strip()
    if requested_crid:
        crid = requested_crid
        reused_rate = True
    elif len(repairable_crids) > 1:
        raise ValueError(
            "Multiple repairable DigiCloud rates exist for RGID "
            f"{rate_group_id} (CRIDs {', '.join(repairable_crids)}). "
            "Repair or remove the duplicates in Platypus before retrying."
        )
    else:
        reused_rate = bool(repairable_crids)
        crid = repairable_crids[0] if reused_rate else await client.add_rate(
            customer_id, rate_group_id, frequency=1, quantity=1
        )
    try:
        try:
            existing_services = await client.list_services2(customer_id, crid=crid)
        except PlatypusAPIError as exc:
            if exc.code == "DATA_ERROR":
                existing_services = []
            else:
                raise
        service_type_id, rows, definition_scope = await _service_definition_for_rate(
            client,
            customer_id=customer_id,
            rate_group_id=rate_group_id,
            crid=crid,
        )
        fields = build_service_fields(rows, values)
        existing_digital_phone = next((
            service for service in existing_services
            if _service_identity(service)[1] == service_type_id
            or "digitalphone" in re.sub(r"[^a-z0-9]", "", _service_identity(service)[0].lower())
        ), None)
        service_created = existing_digital_phone is None
        if existing_digital_phone is None:
            data_id = await client.add_service(
                customer_id,
                service_type_id=service_type_id,
                crid=crid,
                custom_fields=fields,
            )
        else:
            _, _, data_id = _service_identity(existing_digital_phone)
            if not data_id:
                raise ValueError("The existing Digital Phone service did not include its Data ID.")
        removed_services: list[dict[str, str]] = []
        for service in existing_services:
            if not _is_ata_service(service):
                continue
            service_name, wrong_service_type_id, wrong_data_id = _service_identity(service)
            if not wrong_service_type_id or not wrong_data_id:
                raise ValueError(
                    f"The incorrect {service_name or 'ATA'} service could not be removed because its IDs were missing."
                )
            await client.delete_service(
                customer_id,
                service_type_id=wrong_service_type_id,
                data_id=wrong_data_id,
            )
            removed_services.append({
                "name": service_name,
                "service_type_id": wrong_service_type_id,
                "data_id": wrong_data_id,
            })
    except Exception as exc:
        raise DigiCloudBillingProvisionError(
            f"Rate CRID {crid} exists, but the Digital Phone service repair failed: {exc}",
            crid=crid,
        ) from exc
    return {
        "crid": crid,
        "service_data_id": data_id,
        "service_type_id": service_type_id,
        "service_definition_scope": definition_scope,
        "mac_address": mac,
        "reused_rate": reused_rate,
        "service_created": service_created,
        "removed_services": removed_services,
    }
