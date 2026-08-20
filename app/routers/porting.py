from __future__ import annotations

from typing import Any
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.dependencies import bw
from app.database.core import get_db
from app.database.models import PortDraft
from app.services.port_draft_service import add_timeline_event, load_values, record_attempt, record_portability_snapshot, save_draft, values_from_form
from app.services.phone_numbers import normalize_e164, parse_phone_numbers
from app.services.notifications import render_email_template, send_port_email
from app.services.port_notifications import process_port_notification
from app.config import get_settings
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.services.bandwidth import BandwidthAPIError, translate_bandwidth_error
from app.web import render
from app.security import filter_bandwidth_records, require_bandwidth_site, require_platform_staff, visible_bandwidth_sites

router = APIRouter(prefix="/ports")
logger = logging.getLogger("digicloud.porting")


def eastern_timezone():
    """Return the US Eastern timezone, with a Windows-safe fallback.

    Installing the ``tzdata`` package is preferred because the fixed-offset
    fallback cannot apply daylight-saving rules.
    """
    try:
        return ZoneInfo("America/New_York")
    except ZoneInfoNotFoundError:
        logger.warning(
            "IANA timezone data is unavailable; using a fixed UTC-05:00 fallback. "
            "Install tzdata for daylight-saving-aware Eastern time."
        )
        return timezone(timedelta(hours=-5))


EASTERN = eastern_timezone()



def _process_port_notification_safely(db: Session, order: dict[str, Any], *, order_url: str = "") -> list[str]:
    """Notification delivery must never make the porting UI unavailable."""
    try:
        return process_port_notification(db, order, order_url=order_url)
    except Exception:
        logger.exception("Port notification processing failed; continuing without blocking porting UI")
        db.rollback()
        return []


def _normalize_e164(value: str) -> str:
    return normalize_e164(value)


def _numbers(text: str) -> list[str]:
    return parse_phone_numbers(text)


def _get_ci(data: dict[str, Any], *keys: str) -> Any:
    targets = {key.casefold() for key in keys}
    for key, value in data.items():
        if str(key).casefold() in targets:
            return value
    return None



def _format_tn(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return str(value or "")


def _as_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        # Common XML-to-dict wrappers used by Bandwidth.
        for key in ("Tn", "tn", "phoneNumber", "PhoneNumber", "telephoneNumber", "TelephoneNumber"):
            nested = _get_ci(value, key)
            if nested not in (None, ""):
                return _as_list(nested)
        return list(value.values())
    return [value]



def _parse_estimate_datetime(value: Any) -> datetime | None:
    """Parse common Bandwidth estimate timestamp forms without discarding raw values."""
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    candidates = [text]
    if text.endswith("Z"):
        candidates.insert(0, text[:-1] + "+00:00")
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=EASTERN)
            return parsed
        except ValueError:
            pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %I:%M %p", "%b %d %Y %I:%M %p",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=EASTERN)
            return parsed
        except ValueError:
            pass
    return None


def _format_estimate(value: Any) -> str:
    parsed = _parse_estimate_datetime(value)
    if not parsed:
        return str(value or "")
    eastern = parsed.astimezone(EASTERN)
    return f"{eastern.strftime('%b')} {eastern.day}, {eastern.year} {eastern.strftime('%I:%M %p').lstrip('0')} ET"


def _estimate_for_form(value: Any) -> str:
    parsed = _parse_estimate_datetime(value)
    if not parsed:
        return ""
    return parsed.astimezone(EASTERN).strftime("%Y-%m-%dT%H:%M")


def _split_foc_value(value: Any) -> tuple[str, str]:
    """Return date and Eastern time suitable for separate HTML controls."""
    parsed = _parse_estimate_datetime(value)
    if parsed:
        eastern = parsed.astimezone(EASTERN)
        return eastern.strftime("%Y-%m-%d"), eastern.strftime("%H:%M")
    text = str(value or "").strip()
    if "T" in text:
        date_part, time_part = text.split("T", 1)
        return date_part[:10], time_part[:5]
    return text[:10] if len(text) >= 10 else text, ""

def _bandwidth_utc_timestamp(date_value: Any, time_value: Any) -> str:
    """Convert an Eastern local activation date/time to Bandwidth UTC ISO-8601."""
    date_text, embedded_time = _split_foc_value(date_value)
    if not date_text:
        return ""
    selected_time = str(time_value or embedded_time or "11:30").strip()[:5]
    try:
        local_dt = datetime.strptime(f"{date_text} {selected_time}", "%Y-%m-%d %H:%M").replace(tzinfo=EASTERN)
    except ValueError as exc:
        raise ValueError("Requested activation date or time is invalid.") from exc
    utc_dt = local_dt.astimezone(timezone.utc).replace(microsecond=0)
    return utc_dt.isoformat().replace("+00:00", "Z")


def _friendly_eastern(value: Any) -> str:
    parsed = _parse_estimate_datetime(value)
    if not parsed:
        return str(value or "")
    eastern = parsed.astimezone(EASTERN)
    return f"{eastern.strftime('%B')} {eastern.day}, {eastern.year} at {eastern.strftime('%I:%M %p').lstrip('0')} ET"


def _port_profile(port_type: Any, phone_number_type: Any = "") -> dict[str, Any]:
    """Classify Bandwidth port behavior conservatively.

    Only explicitly identified automated port types use timestamp payloads.
    Legacy NSR/LSR values and unknown or missing types use date-only FOC,
    which avoids incorrectly sending an automated-port timestamp.
    """
    port = str(port_type or "").strip().upper()
    number_type = str(phone_number_type or "").strip().upper()

    manual_prefixes = ("NSR", "LSR", "MANUAL")
    wireless_tokens = ("WIRELESS", "MOBILE")
    wireline_tokens = ("WIRELINE", "AUTOMATED WIRELINE", "AUTO-WIRELINE")

    if port.startswith(manual_prefixes) or "MANUAL" in port:
        return {"kind": "manual", "time_editable": False, "triggered": False, "label": "Manual port"}
    if any(token in number_type for token in wireless_tokens) or any(token in port for token in wireless_tokens):
        return {"kind": "automated_wireless", "time_editable": True, "triggered": False, "label": "Automated wireless"}
    if any(token in number_type for token in wireline_tokens) or any(token in port for token in wireline_tokens):
        return {"kind": "automated_wireline", "time_editable": True, "triggered": True, "label": "Automated wireline"}

    # Conservative fallback: a missing/unrecognized type must not be treated
    # as automated wireline. Bandwidth manual/legacy orders expect a date only.
    return {"kind": "manual", "time_editable": False, "triggered": False, "label": "Manual/unknown port"}


def _build_requested_foc(date_value: Any, time_value: Any, port_type: Any, phone_number_type: Any = "") -> tuple[str, bool | None]:
    """Build Bandwidth RequestedFocDate from an Eastern local selection.

    NOP always treats scheduling controls as America/New_York local time and
    converts to UTC only at the provider boundary. This prevents a selected
    calendar date from becoming midnight UTC (the prior-day evening in ET).
    """
    date_text, embedded_time = _split_foc_value(date_value)
    if not date_text:
        return "", None
    profile = _port_profile(port_type, phone_number_type)
    selected_time = str(time_value or embedded_time or "11:30").strip()[:5]
    foc_value = _bandwidth_utc_timestamp(date_text, selected_time)
    logger.info(
        "FOC payload value: profile=%s local=%s %s ET utc=%s",
        profile["kind"], date_text, selected_time, foc_value,
    )
    if profile["kind"] == "automated_wireline":
        return foc_value, selected_time != "11:30"
    return foc_value, None




def _use_earliest_selected(value: Any, *, default: bool = True) -> bool:
    """Parse the scheduling choice without converting a stored False back to True."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "on"}


def _future_estimate_floor(*values: Any) -> str:
    """Return the latest known future scheduling estimate as a UTC ISO value.

    Existing exception orders can receive a stale/past estimate from a fresh
    OnePort lookup for TNs that are already processing.  Never replace a known
    future estimate with that stale value.
    """
    now_utc = datetime.now(timezone.utc)
    parsed = []
    for value in values:
        dt = _parse_estimate_datetime(value)
        if dt is not None and dt > now_utc:
            parsed.append(dt.astimezone(timezone.utc))
    if not parsed:
        return ""
    return max(parsed).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _validate_foc_selection(values: dict[str, Any]) -> str | None:
    """Validate an explicitly requested FOC against Bandwidth's earliest estimate."""
    use_earliest = _use_earliest_selected(values.get("useEarliest"))
    if use_earliest:
        return None
    requested_date, _ = _split_foc_value(values.get("requestedFocDate"))
    earliest_date, _ = _split_foc_value(values.get("earliestEstimate"))
    if not requested_date:
        return "Choose a requested port date or select Use earliest available."
    if earliest_date and requested_date < earliest_date:
        return f"Requested port date cannot be earlier than Bandwidth's earliest available date ({earliest_date})."
    return None


def _portability_summary(data: Any) -> dict[str, Any]:
    """Normalize Bandwidth portability responses into user-facing carrier groups.

    Supports both the legacy XML LNP checker response and the newer JSON
    OnePort portability response. Unknown fields remain available in the raw
    response shown under Technical Details.
    """
    groups: list[dict[str, Any]] = []
    nonportable: list[dict[str, Any]] = []
    discovered_estimates: list[Any] = []

    def value_ci(source: dict[str, Any], *keys: str) -> Any:
        return _get_ci(source, *keys)

    def extract_numbers(source: dict[str, Any]) -> list[str]:
        raw = value_ci(
            source, "phoneNumbers", "PhoneNumbers", "telephoneNumbers",
            "TelephoneNumbers", "TnList", "tnList", "numbers", "Numbers",
            "portablePhoneNumbers", "PortablePhoneNumbers",
        )
        values = _as_list(raw)
        result: list[str] = []
        for item in values:
            if isinstance(item, dict):
                nested = value_ci(item, "phoneNumber", "telephoneNumber", "Tn", "tn")
                if nested not in (None, ""):
                    result.extend(str(v) for v in _as_list(nested))
            elif item not in (None, ""):
                result.append(str(item))
        # Preserve order while removing duplicates.
        return list(dict.fromkeys(result))

    def add_group(source: dict[str, Any]) -> None:
        numbers = extract_numbers(source)
        losing = value_ci(source, "losingCarrier", "LosingCarrier", "carrier", "Carrier", "losingLsp", "LosingLsp")
        carrier_name = ""
        spid = value_ci(source, "spid", "SPID", "carrierSpid", "CarrierSpid") or ""
        if isinstance(losing, dict):
            carrier_name = str(value_ci(losing, "name", "Name", "carrierName", "CarrierName") or "")
            spid = str(value_ci(losing, "spid", "SPID", "id", "Id") or spid or "")
        elif losing not in (None, ""):
            carrier_name = str(losing)

        if not carrier_name:
            carrier_name = str(value_ci(source, "carrierName", "CarrierName", "losingCarrierName", "LosingCarrierName", "lspName", "LspName") or "")

        # Avoid treating generic wrapper objects as carrier groups.
        if not numbers and not carrier_name and not spid:
            return

        rate_center = value_ci(source, "rateCenter", "RateCenter")
        rate_center_name = ""
        if isinstance(rate_center, dict):
            rate_center_name = str(value_ci(rate_center, "name", "Name") or "")
        elif rate_center not in (None, ""):
            rate_center_name = str(rate_center)

        # Bandwidth legacy responses may combine the carrier, SPID, and
        # port type in one display value, for example:
        # "Frontier Rochester:0121 - NSR/1".
        composite_port_type = ""
        if carrier_name:
            match = re.match(r"^\s*(.*?)\s*:\s*([A-Za-z0-9]+)\s*(?:-\s*(.+?))?\s*$", carrier_name)
            if match:
                carrier_name = match.group(1).strip()
                if not spid:
                    spid = match.group(2).strip()
                composite_port_type = (match.group(3) or "").strip()

        group = {
            "carrier_name": carrier_name or "Carrier unavailable",
            "spid": str(spid or ""),
            "phone_numbers": numbers,
            "formatted_numbers": [_format_tn(number) for number in numbers],
            "earliest_estimate": str(value_ci(
                source,
                "earliestEstimate", "EarliestEstimate",
                "earliestPortDate", "EarliestPortDate",
                "earliestPortingDate", "EarliestPortingDate",
                "estimatedPortDate", "EstimatedPortDate",
                "estimatedCompletionDate", "EstimatedCompletionDate",
                "portDate", "PortDate",
                "estimatedDate", "EstimatedDate",
                "earliestDate", "EarliestDate",
            ) or ""),
            "port_type": str(value_ci(source, "portType", "PortType", "networkType", "NetworkType") or composite_port_type or ""),
            "phone_number_type": str(value_ci(source, "phoneNumberType", "PhoneNumberType") or ""),
            "country": str(value_ci(source, "countryCodeA3", "CountryCodeA3", "country", "Country") or ""),
            "rate_center": rate_center_name,
            "resp_org": str(value_ci(source, "respOrg", "RespOrg", "resporg", "Resporg") or ""),
        }
        fingerprint = (group["carrier_name"], group["spid"], tuple(group["phone_numbers"]))
        if fingerprint not in {(g["carrier_name"], g["spid"], tuple(g["phone_numbers"])) for g in groups}:
            groups.append(group)

    def add_nonportable(source: dict[str, Any]) -> None:
        number = value_ci(source, "phoneNumber", "PhoneNumber", "telephoneNumber", "TelephoneNumber", "Tn", "tn")
        reasons = value_ci(source, "reasons", "Reasons", "reason", "Reason")
        if number in (None, ""):
            return
        reason_values = []
        for reason in _as_list(reasons):
            if isinstance(reason, dict):
                reason = value_ci(reason, "description", "Description", "message", "Message", "reason", "Reason")
            if reason not in (None, ""):
                reason_values.append(str(reason))
        record = {"phone_number": str(number), "formatted_number": _format_tn(number), "reasons": reason_values}
        if record not in nonportable:
            nonportable.append(record)

    def walk(value: Any, parent_key: str = "") -> None:
        if isinstance(value, list):
            for item in value:
                walk(item, parent_key)
            return
        if not isinstance(value, dict):
            return

        keys = {str(k).casefold() for k in value}
        for key, candidate in value.items():
            normalized_key = re.sub(r"[^a-z]", "", str(key).casefold())
            if normalized_key in {
                "earliestestimate", "earliestportdate", "earliestportingdate",
                "estimatedportdate", "estimatedcompletiondate", "estimateddate",
                "earliestdate", "portdate", "portingestimatedate",
            } and candidate not in (None, ""):
                if isinstance(candidate, dict):
                    candidate = value_ci(candidate, "date", "Date", "dateTime", "DateTime", "value", "Value")
                if candidate not in (None, ""):
                    discovered_estimates.append(candidate)
        parent = parent_key.casefold()
        is_nonportable = "nonportable" in parent or any("nonportable" in key for key in keys)
        if is_nonportable and keys.intersection({"phonenumber", "telephonenumber", "tn"}):
            add_nonportable(value)
        elif keys.intersection({
            "losingcarrier", "carriername", "losingcarriername", "spid",
            "earliestestimate", "porttype", "phonenumbers", "tnlist"
        }):
            add_group(value)

        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                walk(nested, str(key))

    walk(data)

    # Some legacy checker responses return a single carrier and a separate TN list
    # at different levels. Build a fallback group from all discovered values.
    if not groups and isinstance(data, dict):
        flattened_candidates: list[dict[str, Any]] = []
        def collect(value: Any) -> None:
            if isinstance(value, dict):
                flattened_candidates.append(value)
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)
        collect(data)
        merged: dict[str, Any] = {}
        for candidate in flattened_candidates:
            for key, value in candidate.items():
                merged.setdefault(key, value)
        add_group(merged)

    # Legacy Bandwidth responses often expose the same TN set twice: once
    # in a generic portability/rate-center object and again in the losing-
    # carrier object. Merge those records by TN set so one carrier does not
    # appear as two cards (including a duplicate "Carrier unavailable" card).
    normalized_groups: list[dict[str, Any]] = []
    by_numbers: dict[tuple[str, ...], dict[str, Any]] = {}

    def normalized_tn_set(group: dict[str, Any]) -> tuple[str, ...]:
        values = []
        for number in group.get("phone_numbers", []):
            digits = "".join(ch for ch in str(number) if ch.isdigit())
            if len(digits) == 11 and digits.startswith("1"):
                digits = digits[1:]
            values.append(digits or str(number))
        return tuple(sorted(set(values)))

    def has_real_carrier(group: dict[str, Any]) -> bool:
        return bool(group.get("carrier_name") and group.get("carrier_name") != "Carrier unavailable")

    for group in groups:
        key = normalized_tn_set(group)
        # Groups without TNs cannot safely be correlated; retain them unless
        # they are empty placeholders.
        if not key:
            if has_real_carrier(group) or group.get("spid"):
                normalized_groups.append(group)
            continue

        existing = by_numbers.get(key)
        if existing is None:
            by_numbers[key] = group
            normalized_groups.append(group)
            continue

        # Prefer a named carrier over the generic metadata record.
        if has_real_carrier(group) and not has_real_carrier(existing):
            primary, secondary = group, existing
            index = normalized_groups.index(existing)
            normalized_groups[index] = primary
            by_numbers[key] = primary
        else:
            primary, secondary = existing, group

        # Fill any missing carrier metadata from the duplicate object.
        for field in (
            "carrier_name", "spid", "earliest_estimate", "port_type",
            "phone_number_type", "country", "rate_center", "resp_org",
        ):
            current = primary.get(field)
            candidate = secondary.get(field)
            if (not current or current == "Carrier unavailable") and candidate:
                primary[field] = candidate

        # Keep one canonical ordered TN list and regenerate display values.
        merged_numbers = list(dict.fromkeys(
            list(primary.get("phone_numbers", [])) + list(secondary.get("phone_numbers", []))
        ))
        primary["phone_numbers"] = merged_numbers
        primary["formatted_numbers"] = [_format_tn(number) for number in merged_numbers]

    groups = normalized_groups
    # Remove carrier-only duplicates when the same carrier/SPID already has a
    # canonical group containing telephone numbers.
    represented_carriers = {
        (str(group.get("carrier_name") or "").casefold(), str(group.get("spid") or "").casefold())
        for group in groups if group.get("phone_numbers")
    }
    represented_spids = {
        str(group.get("spid") or "").strip().casefold()
        for group in groups
        if group.get("phone_numbers") and str(group.get("spid") or "").strip()
    }
    groups = [
        group for group in groups
        if group.get("phone_numbers") or (
            (str(group.get("carrier_name") or "").casefold(), str(group.get("spid") or "").casefold()) not in represented_carriers
            and str(group.get("spid") or "").strip().casefold() not in represented_spids
        )
    ]
    unique_estimates = list(dict.fromkeys(str(value) for value in discovered_estimates if value not in (None, "")))
    if len(unique_estimates) == 1:
        for group in groups:
            if group.get("phone_numbers") and not group.get("earliest_estimate"):
                group["earliest_estimate"] = unique_estimates[0]
    for group in groups:
        raw_estimate = group.get("earliest_estimate") or ""
        group["earliest_estimate_raw"] = raw_estimate
        group["earliest_estimate"] = _format_estimate(raw_estimate)
        group["earliest_estimate_form"] = _estimate_for_form(raw_estimate)
        group["earliest_estimate_date"], group["earliest_estimate_time"] = _split_foc_value(raw_estimate)
        group["port_profile"] = _port_profile(group.get("port_type"), group.get("phone_number_type"))
    unique_portable_numbers = {
        "".join(ch for ch in str(number) if ch.isdigit())
        for group in groups for number in group.get("phone_numbers", [])
        if number not in (None, "")
    }
    portable_count = len(unique_portable_numbers)
    return {
        "groups": groups,
        "nonportable": nonportable,
        "portable_count": portable_count,
        "carrier_count": len(groups),
        "multiple_carriers": len(groups) > 1,
    }



_COMPLETED_PORT_STATUSES = {
    "complete", "completed", "cancelled", "canceled", "failed", "partial"
}
_OPEN_PORTOUT_STATUSES = {"pending", "foc", "exception", "in_progress", "in progress", "submitted"}

def _status_text(value: Any) -> str:
    return str(value or "").strip().casefold().replace("-", "_")

def _is_completed_port(status: Any) -> bool:
    text = _status_text(status)
    return text in _COMPLETED_PORT_STATUSES or text.startswith("complete")

def _is_active_exception(status: Any) -> bool:
    text = _status_text(status)
    if _is_completed_port(text):
        return False
    return any(word in text for word in ("exception", "error", "attention", "rejected", "failed"))

def _is_foc_port(item: dict[str, Any]) -> bool:
    status = item.get("processingStatus")
    if _is_completed_port(status) or _is_active_exception(status):
        return False
    text = _status_text(status).replace(" ", "_")
    has_foc_date = bool(
        item.get("actualFocDate")
        or item.get("requestedFocDate")
        or item.get("focDate")
    )
    return has_foc_date or "foc" in text or "firm_order_commitment" in text

def _is_open_port(item: dict[str, Any]) -> bool:
    status = item.get("processingStatus")
    return (
        not _is_completed_port(status)
        and not _is_active_exception(status)
        and not _is_foc_port(item)
    )

def _is_open_portout(status: Any) -> bool:
    text = _status_text(status)
    if not text or _is_completed_port(text):
        return False
    return text in _OPEN_PORTOUT_STATUSES or any(
        word in text for word in ("pending", "progress", "foc", "exception", "submitted")
    )


def _port_items(data: Any) -> list[dict[str, Any]]:
    """Extract port summaries from JSON or XML-shaped Bandwidth responses."""
    found: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return

        order_id = _get_ci(value, "orderId", "id", "OrderId")
        status = _get_ci(value, "processingStatus", "status", "ProcessingStatus")
        if order_id and status:
            found.append(_normalise_port(value))
            return

        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(nested)

    walk(data)
    unique: dict[str, dict[str, Any]] = {}
    for item in found:
        unique[str(item["orderId"])] = item
    return list(unique.values())




def _unwrap_port_detail(data: Any) -> dict[str, Any]:
    """Find and normalize the actual port-in order inside XML/JSON wrappers."""
    candidates: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return
        keys = {str(k).casefold() for k in value}
        if keys.intersection({"processingstatus", "orderid", "requestedfocdate", "actualfocdate", "billingtelephonenumber"}):
            candidates.append(value)
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(nested)

    walk(data)
    source = max(candidates, key=lambda item: len(item), default=data if isinstance(data, dict) else {})

    def pick(*keys: str, default: Any = "") -> Any:
        value = _get_ci(source, *keys)
        return default if value in (None, "") else value

    phone_numbers = pick("phoneNumbers", "telephoneNumbers", "listOfPhoneNumbers", "ListOfPhoneNumbers", default=[])
    if isinstance(phone_numbers, dict):
        phone_numbers = _get_ci(phone_numbers, "telephoneNumber", "phoneNumber", "Tn") or []
    if isinstance(phone_numbers, str):
        phone_numbers = [phone_numbers]
    if not isinstance(phone_numbers, list):
        phone_numbers = []

    subscriber = pick("subscriber", "Subscriber", default={})
    if not isinstance(subscriber, dict):
        subscriber = {}
    losing_carrier = pick("losingCarrier", "LosingCarrier", default={})
    if not isinstance(losing_carrier, dict):
        losing_carrier = {}

    normalized = {
        **source,
        "orderId": pick("orderId", "OrderId", "id"),
        "processingStatus": pick("processingStatus", "ProcessingStatus", "status"),
        "requestedFocDate": pick("requestedFocDate", "RequestedFocDate"),
        "actualFocDate": pick("actualFocDate", "ActualFocDate"),
        "earliestEstimate": pick("earliestEstimate", "EarliestEstimate"),
        "billingTelephoneNumber": pick("billingTelephoneNumber", "BillingTelephoneNumber", "billingPhoneNumber"),
        "customerOrderId": pick("customerOrderId", "CustomerOrderId"),
        "subAccountId": pick("subAccountId", "SubAccountId", "siteId", "SiteId"),
        "locationId": pick("locationId", "LocationId", "sipPeerId", "SipPeerId"),
        "losingCarrierName": pick("losingCarrierName", "LosingCarrierName") or _get_ci(losing_carrier, "name", "Name", "carrierName", "CarrierName") or "",
        "phoneNumbers": phone_numbers,
        "subscriber": subscriber,
        "errors": pick("errors", "Errors", "errorList", "ErrorList", default=[]),
        "raw": data,
    }
    return normalized


def _provider_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _live_order_values(order: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """Overlay provider-authoritative mutable port fields onto a local draft."""
    updated = dict(values or {})
    live_numbers = order.get("phoneNumbers") or []
    if live_numbers:
        updated["phoneNumbers"] = " ".join(str(number) for number in live_numbers)
    if order.get("billingTelephoneNumber"):
        updated["billingTelephoneNumber"] = order.get("billingTelephoneNumber")
    if order.get("subAccountId") not in (None, ""):
        updated["subAccountId"] = order.get("subAccountId")
    if order.get("locationId") not in (None, ""):
        updated["locationId"] = order.get("locationId")
    if order.get("losingCarrierName"):
        updated["losingCarrierName"] = order.get("losingCarrierName")
    requested = order.get("requestedFocDate")
    if requested:
        foc_date, foc_time = _split_foc_value(requested)
        updated["requestedFocDate"] = foc_date
        if foc_time:
            updated["requestedFocTime"] = foc_time
        # A provider-side requested date is an explicit choice, not "earliest".
        updated["useEarliest"] = False
    for target, keys in {
        "portType": ("portType", "PortType"),
        "phoneNumberType": ("phoneNumberType", "PhoneNumberType"),
        "newBillingTelephoneNumber": ("newBillingTelephoneNumber", "NewBillingTelephoneNumber"),
    }.items():
        value = _get_ci(order, *keys)
        if value not in (None, ""):
            updated[target] = value
    return updated


async def _latest_portability_for_edit(values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Refresh carrier/earliest-date metadata without blocking the edit form."""
    try:
        raw = await bw.porting.check_portability(_numbers(str(values.get("phoneNumbers") or "")))
        summary = _portability_summary(raw)
        groups = summary.get("groups") or []
        if len(groups) == 1 and not summary.get("nonportable"):
            return _apply_portability_group(values, groups[0]), summary
        return values, summary
    except (ValueError, BandwidthAPIError):
        return values, None


def _normalise_port(item: dict[str, Any]) -> dict[str, Any]:
    phone_numbers = _get_ci(
        item,
        "phoneNumbers",
        "telephoneNumbers",
        "listOfPhoneNumbers",
        "ListOfPhoneNumbers",
    )
    count = _get_ci(item, "countOfPhoneNumbers", "numberCount", "CountOfPhoneNumbers")
    if not count:
        if isinstance(phone_numbers, list):
            count = len(phone_numbers)
        elif isinstance(phone_numbers, dict):
            nested = _get_ci(phone_numbers, "telephoneNumber", "phoneNumber")
            count = len(nested) if isinstance(nested, list) else (1 if nested else "")

    return {
        **item,
        "orderId": _get_ci(item, "orderId", "id", "OrderId") or "",
        "processingStatus": _get_ci(item, "processingStatus", "status", "ProcessingStatus") or "",
        "billingPhoneNumber": _get_ci(
            item,
            "billingPhoneNumber",
            "billingTelephoneNumber",
            "BillingTelephoneNumber",
            "btn",
        ) or "",
        "losingCarrierName": _get_ci(
            item,
            "losingCarrierName",
            "losingCarrier",
            "LosingCarrierName",
            "vendorName",
        ) or "",
        "countOfPhoneNumbers": count or "",
        "customerOrderId": _get_ci(item, "customerOrderId", "CustomerOrderId") or "",
        "lastModifiedDate": _get_ci(
            item, "lastModifiedDate", "LastModifiedDate", "lastModified", "OrderCreateDate"
        ) or "",
        "subAccountId": _get_ci(item, "subAccountId", "siteId", "SiteId") or "",
    }






def _collect_phone_numbers(value: Any) -> list[str]:
    """Collect TN/BTN values from nested Bandwidth JSON or XML-shaped data."""
    number_keys = {
        "telephone_number", "telephonenumber", "telephone_numbers", "telephonenumbers",
        "phone_number", "phonenumber", "phone_numbers", "phonenumbers",
        "tn", "tns", "tn_list", "tnlist", "number", "numbers",
        "billing_telephone_number", "billingtelephonenumber",
        "billing_phone_number", "billingphonenumber", "btn",
    }
    found: list[str] = []

    def add(raw: Any) -> None:
        if raw in (None, ""):
            return
        if isinstance(raw, (list, tuple, set)):
            for item in raw:
                add(item)
            return
        if isinstance(raw, dict):
            for nested in raw.values():
                add(nested)
            return
        text = str(raw).strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) in (10, 11):
            normalized = "+" + digits if len(digits) == 11 else "+1" + digits
            if normalized not in found:
                found.append(normalized)

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        for key, nested in node.items():
            canonical = "".join(ch if ch.isalnum() else "_" for ch in str(key).casefold()).strip("_")
            compact = canonical.replace("_", "")
            if canonical in number_keys or compact in number_keys:
                add(nested)
            if isinstance(nested, (dict, list)):
                walk(nested)

    walk(value)
    return found

def _portout_items(data: Any) -> list[dict[str, Any]]:
    """Extract LSR/port-out summaries from Bandwidth JSON or XML wrappers."""
    found: list[dict[str, Any]] = []

    def as_list(value: Any) -> list[Any]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        return [value]

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return

        order_id = _get_ci(
            value, "OrderId", "orderId", "PortOutId", "portOutId", "Id", "id"
        )
        pon = _get_ci(value, "PON", "Pon", "pon")
        status = _get_ci(
            value, "Status", "status", "OrderStatus", "orderStatus",
            "ProcessingStatus", "processingStatus"
        )

        # Bandwidth responses vary between JSON and XML and may identify a
        # summary by OrderId or by PON. Accept either, but require a status.
        if status and (order_id or pon):
            numbers = _collect_phone_numbers(value)
            count = _get_ci(
                value, "CountOfTelephoneNumbers", "countOfTelephoneNumbers",
                "CountOfPhoneNumbers", "countOfPhoneNumbers", "NumberCount", "numberCount"
            )
            try:
                count = int(count)
            except (TypeError, ValueError):
                count = len(numbers)

            found.append({
                **value,
                "orderId": str(order_id or pon),
                "status": str(status),
                "pon": str(pon or ""),
                "customerOrderId": str(_get_ci(value, "CustomerOrderId", "customerOrderId") or ""),
                "billingTelephoneNumber": str(_get_ci(
                    value, "BillingTelephoneNumber", "billingTelephoneNumber", "BTN", "btn",
                "BillingPhoneNumber", "billingPhoneNumber"
                ) or ""),
                "requestedFocDate": str(_get_ci(
                    value, "RequestedFocDate", "requestedFocDate", "RequestedFOCDate"
                ) or ""),
                "actualFocDate": str(_get_ci(
                    value, "ActualFocDate", "actualFocDate", "ActualFOCDate"
                ) or ""),
                "lastModifiedDate": str(_get_ci(
                    value, "LastModifiedDate", "lastModifiedDate", "LastModified",
                    "OrderCreateDate", "orderCreateDate", "CreatedDate", "createdDate",
                    "ModifiedDate", "modifiedDate", "CompletedDate", "completedDate"
                ) or ""),
                "phoneNumbers": numbers,
                "numberCount": count,
                "displayNumber": str(
                    _get_ci(
                        value, "BillingTelephoneNumber", "billingTelephoneNumber", "BTN", "btn",
                        "BillingPhoneNumber", "billingPhoneNumber"
                    ) or (numbers[0] if numbers else "")
                ),
            })
            return

        for nested in value.values():
            if isinstance(nested, (dict, list)):
                walk(nested)

    walk(data)
    unique: dict[str, dict[str, Any]] = {}
    for item in found:
        unique[item["orderId"]] = item
    return list(unique.values())

@router.get("", response_class=HTMLResponse)
async def ports(
    request: Request,
    site_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(300, ge=1, le=1000),
    view: str = Query("all"),
    db: Session = Depends(get_db),
):
    sites, portins, error = [], [], None
    if site_id is not None:
        require_bandwidth_site(request, site_id)
    try:
        sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
        portins = filter_bandwidth_records(request, _port_items(await bw.porting.list(page=page, size=size)), "subAccountId", "siteId")
        local_submitted = list(db.scalars(select(PortDraft).where(
            PortDraft.organization_id == request.state.user.organization_id,
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
        if site_id:
            portins = [
                item for item in portins
                if str(item.get("subAccountId", "")) == str(site_id)
            ]
        notification_changed = False
        for item in portins:
            sent_events = _process_port_notification_safely(
                db, item,
                order_url=f"{str(request.base_url).rstrip('/')}/ports/{item.get('orderId', '')}",
            )
            notification_changed = notification_changed or bool(sent_events)
        if notification_changed:
            db.commit()
        view = view if view in {"all", "open", "foc", "exception", "completed"} else "all"
        if view == "open":
            portins = [item for item in portins if _is_open_port(item)]
        elif view == "foc":
            portins = [item for item in portins if _is_foc_port(item)]
        elif view == "exception":
            # Only unresolved exceptions belong here. A terminal/completed order
            # is never kept in Exceptions even when old notes mention an error.
            portins = [
                item for item in portins
                if _is_active_exception(item.get("processingStatus"))
            ]
        elif view == "completed":
            portins = [
                item for item in portins
                if _is_completed_port(item.get("processingStatus"))
            ]
    except BandwidthAPIError as exc:
        error = exc.diagnostic
    return render(
        request,
        "ports.html",
        sites=sites,
        selected_site_id=site_id,
        portins=portins,
        error=error,
        page=page,
        size=size,
        view=view,
    )


@router.get("/port-outs", response_class=HTMLResponse)
async def port_outs(
    request: Request,
    btn: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=300),
):
    require_platform_staff(request)
    orders, error = [], None
    try:
        orders = _portout_items(await bw.porting.list_portouts(page=page, size=size))

        # The Bandwidth port-out list response may contain only summary fields.
        # Enrich summaries that omit BTN/TNs by retrieving their order details.
        missing = [order for order in orders if not order.get("displayNumber") and not order.get("phoneNumbers")]
        if missing:
            semaphore = asyncio.Semaphore(8)

            async def enrich(order: dict[str, Any]) -> None:
                async with semaphore:
                    try:
                        detail = await bw.porting.get_portout(order["orderId"])
                    except BandwidthAPIError:
                        return
                    parsed = _portout_items(detail)
                    detail_order = next(
                        (item for item in parsed if str(item.get("orderId")) == str(order.get("orderId"))),
                        parsed[0] if parsed else None,
                    )
                    numbers = (detail_order or {}).get("phoneNumbers") or _collect_phone_numbers(detail)
                    if numbers:
                        order["phoneNumbers"] = numbers
                        order["numberCount"] = len(numbers)
                        order["displayNumber"] = numbers[0]
                    if detail_order:
                        for key in ("billingTelephoneNumber", "pon", "requestedFocDate", "actualFocDate", "lastModifiedDate"):
                            if not order.get(key) and detail_order.get(key):
                                order[key] = detail_order[key]

            await asyncio.gather(*(enrich(order) for order in missing[:100]))

        query_digits = "".join(ch for ch in btn if ch.isdigit())
        if len(query_digits) == 11 and query_digits.startswith("1"):
            query_digits = query_digits[1:]
        if query_digits:
            def includes_btn(order: dict[str, Any]) -> bool:
                candidates = [order.get("billingTelephoneNumber", ""), *order.get("phoneNumbers", [])]
                return any("".join(ch for ch in str(value) if ch.isdigit()).endswith(query_digits) for value in candidates)
            orders = [order for order in orders if includes_btn(order)]
    except BandwidthAPIError as exc:
        error = exc.diagnostic
    open_orders = [order for order in orders if _is_open_portout(order.get("status"))]
    closed_orders = [order for order in orders if _is_completed_port(order.get("status"))]
    # Unknown states are safer to expose as open rather than silently hiding them.
    classified_ids = {item["orderId"] for item in [*open_orders, *closed_orders]}
    open_orders.extend(order for order in orders if order.get("orderId") not in classified_ids)
    open_orders.sort(key=lambda item: str(item.get("lastModifiedDate", "")), reverse=True)
    closed_orders.sort(key=lambda item: str(item.get("lastModifiedDate", "")), reverse=True)
    return render(
        request, "port_outs.html", portouts=orders, open_portouts=open_orders,
        closed_portouts=closed_orders, error=error, page=page, size=size, btn=btn
    )


@router.get("/port-outs/{order_id}", response_class=HTMLResponse)
async def port_out_detail(request: Request, order_id: str):
    require_platform_staff(request)
    try:
        order = await bw.porting.get_portout(order_id)
        return render(request, "port_out_detail.html", order=order, order_id=order_id, error=None)
    except BandwidthAPIError as exc:
        return render(request, "port_out_detail.html", order={}, order_id=order_id, error=exc.diagnostic)


async def _port_form_options(request: Request) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    sites = visible_bandwidth_sites(request, await bw.inventory.list_sites())
    locations_by_site: dict[str, list[dict[str, Any]]] = {}
    for site in sites:
        site_id = site.get("id")
        try:
            locations_by_site[str(site_id)] = await bw.inventory.list_locations(site_id)
        except BandwidthAPIError:
            locations_by_site[str(site_id)] = []
    return sites, locations_by_site


def _validate_btn_workflow(values: dict[str, Any]) -> str | None:
    port_numbers = _numbers(str(values.get("phoneNumbers") or ""))
    normalized_port_numbers = {re.sub(r"\D", "", number)[-10:] for number in port_numbers}
    normalized_btn = re.sub(r"\D", "", str(values.get("billingTelephoneNumber") or ""))[-10:]
    normalized_new_btn = re.sub(r"\D", "", str(values.get("newBillingTelephoneNumber") or ""))[-10:]
    is_full_port = bool(values.get("portingAllNumbers"))
    btn_is_porting = bool(normalized_btn and normalized_btn in normalized_port_numbers)
    if not normalized_btn:
        return "Billing Telephone Number (BTN) is required."
    if not is_full_port and btn_is_porting and not normalized_new_btn:
        return "A new BTN is required because the current BTN is porting while other numbers or services will remain."
    if normalized_new_btn and normalized_new_btn in normalized_port_numbers:
        return "The new BTN must remain with the losing carrier and cannot be included in the porting number list."
    return None


def _port_order_response_details(value: Any) -> tuple[str, str]:
    """Return the provider order id and processing status from nested API responses."""
    if not isinstance(value, dict):
        return "", ""
    response = value.get("LnpOrderResponse") or value.get("lnpOrderResponse") or value
    if not isinstance(response, dict):
        return "", ""
    order_id = str(response.get("OrderId") or response.get("orderId") or response.get("id") or "").strip()
    status = str(response.get("ProcessingStatus") or response.get("processingStatus") or response.get("status") or "").strip().upper()
    return order_id, status


def _provider_draft_from_attempts(draft: Any) -> tuple[str, dict[str, Any]]:
    """Recover a provider-side draft created by an earlier submission attempt."""
    for attempt in reversed(list(getattr(draft, "attempts", []) or [])):
        try:
            response = json.loads(attempt.response_json or "{}")
            request_payload = json.loads(attempt.request_json or "{}")
        except (TypeError, ValueError):
            continue
        order_id, status = _port_order_response_details(response)
        if order_id and status == "DRAFT":
            return order_id, request_payload if isinstance(request_payload, dict) else {}
    return "", {}


def _build_port_payload(values: dict[str, Any]) -> dict[str, Any]:
    is_full_port = bool(values.get("portingAllNumbers"))
    payload: dict[str, Any] = {
        "loaAuthorizingPerson": values["loaAuthorizingPerson"],
        "subAccountId": int(values["subAccountId"]),
        "locationId": int(values["locationId"]),
        "phoneNumbers": _numbers(str(values["phoneNumbers"])),
        "processingStatus": "DRAFT",
        "partialPort": not is_full_port,
        "subscriber": {
            "subscriberType": values["accountType"],
            "businessName": values["customerName"] if values["accountType"] == "BUSINESS" else "",
            "firstName": values["customerName"] if values["accountType"] == "RESIDENTIAL" else "",
            "serviceAddress": {
                "houseNumber": values["streetNumber"],
                "streetName": values["streetName"],
                "addressLine2": values.get("address2") or "",
                "city": values["city"],
                "stateCode": values["state"],
                "zip": values["zip"],
                "plusFour": values.get("zip4") or "",
            },
        },
    }
    # The Port-Ins API does not permit account credentials in Subscriber.
    # They are sent only for wireless ports, inside WirelessInfo. For wireline/
    # geographic ports the values remain stored in the draft but are omitted
    # from the carrier request.
    phone_number_type = str(values.get("phoneNumberType") or "").strip().upper()
    is_wireless = phone_number_type in {"WIRELESS", "MOBILE"} or "WIRELESS" in phone_number_type
    if is_wireless:
        wireless_info: dict[str, str] = {}
        if values.get("accountNumber"):
            wireless_info["accountNumber"] = str(values["accountNumber"]).strip()
        if values.get("accountPin"):
            wireless_info["pinNumber"] = str(values["accountPin"]).strip()
        if wireless_info:
            payload["wirelessInfo"] = wireless_info

    optional_map = {
        "billingTelephoneNumber": "billingTelephoneNumber",
        "losingCarrierName": "losingCarrierName",
        "newBillingTelephoneNumber": "newBillingTelephoneNumber",
    }
    for target, source in optional_map.items():
        if values.get(source):
            payload[target] = (
                _normalize_e164(str(values[source]))
                if target in {"billingTelephoneNumber", "newBillingTelephoneNumber"}
                else values[source]
            )

    use_earliest = _use_earliest_selected(values.get("useEarliest"))
    if not use_earliest:
        foc_value, triggered = _build_requested_foc(
            values.get("requestedFocDate"),
            values.get("requestedFocTime"),
            values.get("portType"),
            values.get("phoneNumberType"),
        )
        if foc_value:
            payload["requestedFocDate"] = foc_value
        if triggered is True:
            payload["triggered"] = True
    else:
        # Match the Bandwidth portal workflow: the portability estimate becomes
        # the default requested activation unless the user chooses a later one.
        earliest_date, earliest_time = _split_foc_value(values.get("earliestEstimate"))
        if earliest_date:
            foc_value, triggered = _build_requested_foc(
                earliest_date, earliest_time or "11:30",
                values.get("portType"), values.get("phoneNumberType"),
            )
            payload["requestedFocDate"] = foc_value
            if triggered is True:
                payload["triggered"] = True
            logger.info("Using current Bandwidth earliest available FOC: %s", foc_value)
        else:
            logger.info("No earliest estimate available; requestedFocDate omitted")
    return payload




def _canonical_snapshot_value(key: str, value: Any) -> str:
    """Normalize portability values so harmless formatting differences do not trigger review."""
    text = str(value or "").strip()
    if not text:
        return ""
    if key == "earliestEstimate":
        parsed = _parse_estimate_datetime(text)
        if parsed:
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    return " ".join(text.upper().split())


def _blocking_nonportable_for_existing_order(summary: dict[str, Any], current_numbers: list[str]) -> list[dict[str, Any]]:
    """Return only nonportable results that should block an existing-order correction.

    OnePort reports TNs that are already on the current submitted order as
    nonportable with the reason "Phone number is currently being processed on
    another order".  For correction/resubmission of that same order, those
    existing TNs are expected and must not block adding/removing other numbers.
    New TNs with that reason, or any TN with another nonportable reason, still
    block the change.
    """
    current = {_normalize_e164(str(n)) for n in current_numbers if str(n).strip()}
    blocking: list[dict[str, Any]] = []
    expected_reason = "phone number is currently being processed on another order"
    for item in summary.get("nonportable") or []:
        number = _normalize_e164(str(item.get("phone_number") or item.get("formatted_number") or ""))
        reasons = [str(r).strip().lower().rstrip(".") for r in (item.get("reasons") or []) if str(r).strip()]
        only_existing_order_reason = bool(reasons) and all(r == expected_reason for r in reasons)
        if number in current and only_existing_order_reason:
            continue
        blocking.append(item)
    return blocking


def _snapshot_fields(values: dict[str, Any]) -> dict[str, str]:
    keys = ("earliestEstimate", "losingCarrierName", "portType", "phoneNumberType", "rateCenter")
    return {key: _canonical_snapshot_value(key, values.get(key)) for key in keys}


def _apply_portability_group(values: dict[str, Any], group: dict[str, Any]) -> dict[str, Any]:
    updated = dict(values)
    updated["earliestEstimate"] = group.get("earliest_estimate_raw") or ""
    updated["losingCarrierName"] = group.get("carrier_name") or ""
    updated["portType"] = group.get("port_type") or ""
    updated["phoneNumberType"] = group.get("phone_number_type") or ""
    updated["rateCenter"] = group.get("rate_center") or ""
    return updated


def _friendly_field_name(key: str) -> str:
    return {
        "earliestEstimate": "Earliest available port date",
        "losingCarrierName": "Losing carrier",
        "portType": "Port handling",
        "phoneNumberType": "Number type",
        "rateCenter": "Rate center",
    }.get(key, key)


async def _refresh_draft_portability(
    db: Session,
    request: Request,
    draft: PortDraft,
    values: dict[str, Any],
    *,
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Refresh OnePort data and return one simple verification result."""
    verified_at = datetime.now(timezone.utc)
    try:
        raw = await bw.porting.check_portability(_numbers(str(values.get("phoneNumbers") or "")))
        summary = _portability_summary(raw)
        groups = summary.get("groups") or []
        existing_provider_order = bool(str(getattr(draft, "bandwidth_order_id", "") or "").strip())
        blocking_nonportable = list(summary.get("nonportable") or [])
        if existing_provider_order and blocking_nonportable:
            try:
                provider_order = _unwrap_port_detail(await bw.porting.get(str(draft.bandwidth_order_id)))
                provider_current_numbers = list(provider_order.get("phoneNumbers") or [])
            except Exception:
                provider_current_numbers = []
            if provider_current_numbers:
                blocking_nonportable = _blocking_nonportable_for_existing_order(summary, provider_current_numbers)

        if blocking_nonportable:
            detail = "One or more telephone numbers are not portable."
            filtered_summary = dict(summary)
            filtered_summary["nonportable"] = blocking_nonportable
            record_portability_snapshot(db, draft, raw, filtered_summary, changed=True, change_summary=detail)
            add_timeline_event(db, draft, "portability_attention", "Portability requires review", detail, severity="warning", user_id=request.state.user.id)
            draft.status = "requires_attention"
            db.commit()
            return values, {"status": "failed", "message": detail, "changes": [], "verified_at": verified_at}

        # New ports must remain a single portability group because NOP uses that
        # group to derive carrier/type/earliest-date metadata before creating the
        # provider order. Existing Bandwidth orders are different: an EXCEPTION
        # correction can legitimately return multiple OnePort groups after TNs
        # are added/removed. In that case Bandwidth's existing-order PUT is the
        # authority on whether the revised number set is allowed. Do not block
        # correction/resubmission locally or overwrite the order metadata with an
        # arbitrary group.
        if len(groups) != 1:
            if existing_provider_order:
                # Preserve carrier/type metadata for an existing order, but still
                # refresh the scheduling floor.  When TNs are added during an
                # exception correction OnePort may return multiple groups; the
                # latest earliest-estimate across those groups is the safe date
                # that applies to the corrected order.
                group_estimates = []
                for group in groups:
                    estimate = group.get("earliest_estimate_raw") or group.get("earliest_estimate") or ""
                    parsed = _parse_estimate_datetime(estimate)
                    if parsed:
                        group_estimates.append(parsed)
                if group_estimates:
                    latest_estimate = max(group_estimates)
                    future_floor = _future_estimate_floor(
                        values.get("earliestEstimate"),
                        latest_estimate.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    )
                    if future_floor:
                        values["earliestEstimate"] = future_floor

                detail = (
                    "Portability returned multiple carrier groups for this existing order. "
                    "NOP preserved the current order metadata, refreshed the scheduling floor, "
                    "and will let Bandwidth validate the revised telephone-number set when the correction is submitted."
                )
                record_portability_snapshot(db, draft, raw, summary, changed=False, change_summary=detail)
                draft.payload_json = json.dumps(values, default=str, separators=(",", ":"))
                draft.updated_at = verified_at
                if draft.status in {"portability_changed", "requires_attention"}:
                    draft.status = "ready_to_submit" if reason == "submission" else "ready_for_review"
                add_timeline_event(
                    db, draft, "portability_verified", "Portability checked for existing order",
                    detail, severity="info", user_id=request.state.user.id,
                )
                db.commit()
                return values, {
                    "status": "ready",
                    "message": detail,
                    "changes": [],
                    "verified_at": verified_at,
                    "multiple_groups": True,
                }

            detail = "The number set is no longer a single portable carrier group."
            record_portability_snapshot(db, draft, raw, summary, changed=True, change_summary=detail)
            add_timeline_event(db, draft, "portability_attention", "Portability requires review", detail, severity="warning", user_id=request.state.user.id)
            draft.status = "requires_attention"
            db.commit()
            return values, {"status": "failed", "message": detail, "changes": [], "verified_at": verified_at}

        before = _snapshot_fields(values)
        prior_earliest = values.get("earliestEstimate")
        updated = _apply_portability_group(values, groups[0])
        if existing_provider_order:
            # A portability lookup for an already-processing TN can return the
            # original (now-past) earliest date. Preserve the latest known future
            # estimate instead of regressing the scheduling floor.
            future_floor = _future_estimate_floor(prior_earliest, updated.get("earliestEstimate"))
            if future_floor:
                updated["earliestEstimate"] = future_floor
        after = _snapshot_fields(updated)

        # Missing values in an older draft are hydrated, not treated as a change.
        changed_keys = [key for key in before if before[key] and before[key] != after[key]]
        changes = [
            {
                "field": _friendly_field_name(key),
                "before": str(values.get(key) or "Not set"),
                "after": str(updated.get(key) or "Not set"),
            }
            for key in changed_keys
        ]
        changed = bool(changes)
        change_summary = "; ".join(f"{item['field']}: {item['before']} → {item['after']}" for item in changes)

        record_portability_snapshot(db, draft, raw, summary, changed=changed, change_summary=change_summary)
        draft.payload_json = json.dumps(updated, default=str, separators=(",", ":"))
        draft.losing_carrier_name = updated.get("losingCarrierName", "")
        draft.updated_at = verified_at
        if changed:
            draft.status = "portability_changed"
            add_timeline_event(db, draft, "portability_changed", "Portability information changed", change_summary, severity="warning", user_id=request.state.user.id)
            status = "changed"
            message = "Portability information was refreshed. Review the changes before submitting."
        else:
            # Clear stale warning states after a successful unchanged verification.
            if draft.status in {"portability_changed", "requires_attention"}:
                draft.status = "draft" if reason == "editing" else "ready_to_submit"
            add_timeline_event(db, draft, "portability_verified", "Portability verified", f"Current portability information was verified before {reason}.", severity="success", user_id=request.state.user.id)
            status = "ready"
            message = "No changes were detected."
        db.commit()
        return updated, {"status": status, "message": message, "changes": changes, "verified_at": verified_at}
    except (ValueError, BandwidthAPIError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else str((exc.diagnostic or {}).get("message") or "Portability verification is temporarily unavailable.")
        add_timeline_event(db, draft, "portability_refresh_failed", "Portability refresh failed", detail, severity="danger", user_id=request.state.user.id)
        draft.status = "requires_attention"
        db.commit()
        return values, {"status": "failed", "message": detail, "changes": [], "verified_at": verified_at}


def _draft_for_user(db: Session, request: Request, draft_id: str) -> PortDraft:
    draft = db.get(PortDraft, draft_id)
    user = request.state.user
    if not draft or not user or draft.organization_id != user.organization_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.get("/drafts", response_class=HTMLResponse)
async def draft_list(request: Request, db: Session = Depends(get_db)):
    user = request.state.user

    # A provider order is no longer a draft, even if an older local row still
    # carries a pre-submit workflow status such as ready_to_schedule.  Reconcile
    # those legacy rows against the live provider list before rendering Drafts.
    # This also repairs records from older builds where Bandwidth accepted the
    # order but local post-submit processing failed before the order id/status
    # was persisted.
    try:
        provider_orders = filter_bandwidth_records(
            request,
            _port_items(await bw.porting.list(page=1, size=1000)),
            "subAccountId",
            "siteId",
        )
        by_reference = {
            str(item.get("customerOrderId") or "").strip(): item
            for item in provider_orders
            if str(item.get("customerOrderId") or "").strip()
        }
        candidates = list(db.scalars(
            select(PortDraft).where(
                PortDraft.organization_id == user.organization_id,
                PortDraft.bandwidth_order_id.is_(None),
            )
        ))
        reconciled = False
        for draft in candidates:
            live = by_reference.get(str(draft.nti_reference or "").strip())
            if not live:
                continue
            order_id = str(live.get("orderId") or "").strip()
            if not order_id:
                continue
            provider_status = str(
                live.get("processingStatus")
                or live.get("status")
                or "SUBMITTED"
            ).strip().upper()
            draft.bandwidth_order_id = order_id
            draft.bandwidth_status = provider_status or "SUBMITTED"
            draft.status = "submitted"
            draft.last_error_code = ""
            draft.last_error_message = ""
            reconciled = True
        if reconciled:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Unable to reconcile submitted port orders while loading Drafts")

    # Drafts means local, not-yet-created provider orders only. Existing live
    # Bandwidth orders belong under Open / FOC / Exceptions / Completed.
    drafts = list(db.scalars(
        select(PortDraft)
        .where(
            PortDraft.organization_id == user.organization_id,
            PortDraft.bandwidth_order_id.is_(None),
            PortDraft.status.notin_(["submitted", "completed", "cancelled", "canceled"]),
        )
        .order_by(PortDraft.updated_at.desc())
    ))
    return render(request, "port_drafts.html", drafts=drafts)


@router.post("/drafts/save")
async def draft_save(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    values = values_from_form(form)
    draft = save_draft(
        db, request.state.user, values,
        draft_id=str(form.get("draft_id") or "") or None,
        status=str(form.get("draft_status") or "draft"),
    )
    return RedirectResponse(f"/ports/drafts/{draft.id}", 303)


@router.get("/drafts/{draft_id}", response_class=HTMLResponse)
async def draft_detail(request: Request, draft_id: str, db: Session = Depends(get_db)):
    draft = _draft_for_user(db, request, draft_id)
    return render(request, "port_draft_detail.html", draft=draft, values=load_values(draft))


@router.get("/drafts/{draft_id}/edit", response_class=HTMLResponse)
async def draft_edit(request: Request, draft_id: str, db: Session = Depends(get_db)):
    draft = _draft_for_user(db, request, draft_id)
    values = load_values(draft)

    # Existing Bandwidth orders are authoritative for the current TN list and
    # requested activation date. This prevents a correction form from showing
    # stale scheduling data that was captured when the draft was first created.
    if draft.bandwidth_order_id:
        try:
            live = _unwrap_port_detail(await bw.porting.get(draft.bandwidth_order_id))
            require_bandwidth_site(request, live.get("subAccountId"))
            values = _live_order_values(live, values)
        except BandwidthAPIError:
            pass

    # Refresh OnePort metadata for the current number set so the earliest
    # available date is current, but never block the user from editing the TNs.
    values, _ = await _latest_portability_for_edit(values)
    draft.payload_json = json.dumps(values, default=str, separators=(",", ":"))
    draft.losing_carrier_name = str(values.get("losingCarrierName") or draft.losing_carrier_name or "")
    db.commit()

    sites, locations_by_site = await _port_form_options(request)
    return render(
        request, "port_new.html", sites=sites, locations_by_site=locations_by_site,
        phoneNumbers=values.get("phoneNumbers", ""), error=None, form_values=values,
        edit_notice=(
            f"Editing {draft.nti_reference}. Current Bandwidth order data was refreshed. "
            "Telephone numbers may be added or removed and will be rechecked before review."
        ),
        verification=None, draft=draft,
    )

@router.post("/drafts/{draft_id}/delete")
async def draft_delete(request: Request, draft_id: str, db: Session = Depends(get_db)):
    draft = _draft_for_user(db, request, draft_id)
    if draft.status == "submitted" and draft.bandwidth_order_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Submitted orders cannot be deleted from Drafts.")
    db.delete(draft)
    db.commit()
    return RedirectResponse("/ports/drafts", 303)


@router.get("/new", response_class=HTMLResponse)
async def new_port(request: Request):
    return render(request, "port_check.html", error=None, phone_numbers="", result=None)


@router.post("/check", response_class=HTMLResponse)
async def check_portability(request: Request, phoneNumbers: str = Form(...)):
    try:
        result = await bw.porting.check_portability(_numbers(phoneNumbers))
        portability = _portability_summary(result)

        # Preserve the single-group OnePort metadata in the signed session as a
        # server-side fallback. Hidden fields are still submitted by the page,
        # but this prevents the earliest estimate and port profile from being
        # lost during the Step 1 -> Step 2 transition.
        groups = portability.get("groups") or []
        if len(groups) == 1:
            group = groups[0]
            request.session["portability_context"] = {
                "phoneNumbers": phoneNumbers,
                "losingCarrierName": group.get("carrier_name") or "",
                "earliestEstimate": group.get("earliest_estimate_raw") or "",
                "portType": group.get("port_type") or "",
                "phoneNumberType": group.get("phone_number_type") or "",
            }
        else:
            request.session.pop("portability_context", None)

        return render(
            request,
            "port_check.html",
            error=None,
            phone_numbers=phoneNumbers,
            result=result,
            portability=portability,
        )
    except ValueError as exc:
        return render(
            request,
            "port_check.html",
            error={"message": str(exc), "payload": {}},
            phone_numbers=phoneNumbers,
            result=None,
        )
    except BandwidthAPIError as exc:
        return render(
            request,
            "port_check.html",
            error=exc.diagnostic,
            phone_numbers=phoneNumbers,
            result=None,
        )


@router.post("/new/details", response_class=HTMLResponse)
async def port_details(
    request: Request,
    phoneNumbers: str = Form(...),
    loaAuthorizingPerson: str = Form(""),
    subAccountId: str = Form(""),
    locationId: str = Form(""),
    billingTelephoneNumber: str = Form(""),
    accountType: str = Form("BUSINESS"),
    customerName: str = Form(""),
    accountNumber: str = Form(""),
    accountPin: str = Form(""),
    streetNumber: str = Form(""),
    streetName: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    zip: str = Form(""),
    zip4: str = Form(""),
    losingCarrierName: str = Form(""),
    requestedFocDate: str = Form(""),
    requestedFocTime: str = Form(""),
    earliestEstimate: str = Form(""),
    useEarliest: str = Form("true"),
    portType: str = Form(""),
    phoneNumberType: str = Form(""),
    portingAllNumbers: str | None = Form(None),
    newBillingTelephoneNumber: str = Form(""),
    edit_notice: str = Form(""),
    draft_id: str = Form(""),
    db: Session = Depends(get_db),
):
    """Render or restore the port-details form without exposing raw 422 errors."""
    sites, locations_by_site = await _port_form_options(request)

    # Use the signed-session copy when a browser/template transition omits the
    # hidden OnePort fields. Only apply it when it belongs to the same TN input.
    context = request.session.get("portability_context") or {}
    if str(context.get("phoneNumbers") or "").strip() == str(phoneNumbers or "").strip():
        losingCarrierName = losingCarrierName or str(context.get("losingCarrierName") or "")
        earliestEstimate = earliestEstimate or str(context.get("earliestEstimate") or "")
        portType = portType or str(context.get("portType") or "")
        phoneNumberType = phoneNumberType or str(context.get("phoneNumberType") or "")

    # Always preserve portability metadata passed from Step 1.  The initial
    # transition may contain only phoneNumbers plus hidden OnePort fields, so
    # gating this dictionary on customer fields discards earliestEstimate.
    form_values = {
        "loaAuthorizingPerson": loaAuthorizingPerson,
        "subAccountId": subAccountId,
        "locationId": locationId,
        "phoneNumbers": phoneNumbers,
        "billingTelephoneNumber": billingTelephoneNumber,
        "accountType": accountType,
        "customerName": customerName,
        "accountNumber": accountNumber,
        "accountPin": accountPin,
        "streetNumber": streetNumber,
        "streetName": streetName,
        "address2": address2,
        "city": city,
        "state": state,
        "zip": zip,
        "zip4": zip4,
        "losingCarrierName": losingCarrierName,
        "requestedFocDate": _split_foc_value(requestedFocDate)[0],
        "requestedFocTime": requestedFocTime or "11:30",
        "earliestEstimate": earliestEstimate,
        "useEarliest": _use_earliest_selected(useEarliest),
        "portType": portType,
        "phoneNumberType": phoneNumberType,
        "portingAllNumbers": portingAllNumbers is not None,
        "newBillingTelephoneNumber": newBillingTelephoneNumber,
    }
    return render(
        request,
        "port_new.html",
        sites=sites,
        locations_by_site=locations_by_site,
        phoneNumbers=phoneNumbers,
        error=None,
        form_values=form_values,
        edit_notice=edit_notice,
        draft=(_draft_for_user(db, request, draft_id) if draft_id else None),
    )


@router.post("/new", response_class=HTMLResponse)
async def review_port(
    request: Request,
    loaAuthorizingPerson: str = Form(...),
    subAccountId: int = Form(...),
    locationId: int = Form(...),
    phoneNumbers: str = Form(...),
    billingTelephoneNumber: str = Form(""),
    accountType: str = Form("BUSINESS"),
    customerName: str = Form(""),
    accountNumber: str = Form(""),
    accountPin: str = Form(""),
    streetNumber: str = Form(""),
    streetName: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    zip: str = Form(""),
    zip4: str = Form(""),
    losingCarrierName: str = Form(""),
    requestedFocDate: str = Form(""),
    requestedFocTime: str = Form(""),
    earliestEstimate: str = Form(""),
    useEarliest: str = Form("true"),
    portType: str = Form(""),
    phoneNumberType: str = Form(""),
    portingAllNumbers: str | None = Form(None),
    newBillingTelephoneNumber: str = Form(""),
    draft_id: str = Form(""),
    db: Session = Depends(get_db),
):
    """Validate and display a review screen without creating a Bandwidth order."""
    require_bandwidth_site(request, subAccountId)
    values = {
        "loaAuthorizingPerson": loaAuthorizingPerson,
        "subAccountId": subAccountId,
        "locationId": locationId,
        "phoneNumbers": phoneNumbers,
        "billingTelephoneNumber": billingTelephoneNumber,
        "accountType": accountType,
        "customerName": customerName,
        "accountNumber": accountNumber,
        "accountPin": accountPin,
        "streetNumber": streetNumber,
        "streetName": streetName,
        "address2": address2,
        "city": city,
        "state": state,
        "zip": zip,
        "zip4": zip4,
        "losingCarrierName": losingCarrierName,
        "requestedFocDate": requestedFocDate,
        "requestedFocTime": requestedFocTime,
        "earliestEstimate": earliestEstimate,
        "useEarliest": _use_earliest_selected(useEarliest),
        "portType": portType,
        "phoneNumberType": phoneNumberType,
        "portingAllNumbers": portingAllNumbers is not None,
        "newBillingTelephoneNumber": newBillingTelephoneNumber,
    }
    draft = save_draft(db, request.state.user, values, draft_id=draft_id or None, status="ready_for_review")

    # For an edited/resubmitted draft, the telephone-number list is editable.
    # Re-run OnePort here so carrier metadata is based on the new set instead
    # of the original order. This also catches a multi-carrier selection while
    # keeping the user on the editable form rather than blocking the GET page.
    if draft_id:
        values, verification = await _refresh_draft_portability(
            db, request, draft, values, reason="review"
        )
        if verification["status"] in {"changed", "failed"}:
            sites, locations_by_site = await _port_form_options(request)
            return render(
                request, "port_new.html", sites=sites, locations_by_site=locations_by_site,
                phoneNumbers=values.get("phoneNumbers", phoneNumbers), error=None,
                verification=verification, form_values=values, draft=draft,
                edit_notice=(
                    f"Editing {draft.nti_reference}. Adjust the telephone-number list "
                    "and review again."
                ),
            )

    validation_error = _validate_btn_workflow(values) or _validate_foc_selection(values)
    if validation_error:
        sites, locations_by_site = await _port_form_options(request)
        return render(
            request, "port_new.html", sites=sites,
            locations_by_site=locations_by_site, phoneNumbers=phoneNumbers,
            error={"message": validation_error, "payload": {}}, form_values=values, draft=draft,
        )

    site_name = str(subAccountId)
    location_name = str(locationId)
    sites, locations_by_site = await _port_form_options(request)
    for site in sites:
        if str(site.get("id")) == str(subAccountId):
            site_name = site.get("name") or site_name
            break
    for location in locations_by_site.get(str(subAccountId), []):
        if str(location.get("id")) == str(locationId):
            location_name = location.get("name") or location_name
            break

    return render(
        request,
        "port_review.html",
        values=values,
        phone_numbers=_numbers(phoneNumbers),
        site_name=site_name,
        location_name=location_name,
        draft=draft,
    )


@router.post("/new/schedule", response_class=HTMLResponse)
async def new_port_schedule(request: Request, draft_id: str = Form(...), db: Session = Depends(get_db)):
    """Final scheduling step before a live Bandwidth submission."""
    draft = _draft_for_user(db, request, draft_id)
    if not draft:
        return RedirectResponse("/ports/new?error=Port+draft+not+found", 303)
    values = load_values(draft)
    values, verification = await _refresh_draft_portability(db, request, draft, values, reason="final_schedule")
    if verification["status"] == "failed":
        sites, locations_by_site = await _port_form_options(request)
        return render(request, "port_new.html", sites=sites, locations_by_site=locations_by_site,
                      phoneNumbers=values.get("phoneNumbers", ""), error=None, verification=verification,
                      form_values=values, draft=draft)
    effective_estimate = _future_estimate_floor(values.get("earliestEstimate"))
    if effective_estimate:
        values["earliestEstimate"] = effective_estimate
    earliest_date, earliest_time = _split_foc_value(values.get("earliestEstimate"))
    today_eastern = datetime.now(EASTERN).date().isoformat()
    if not earliest_date or earliest_date < today_eastern:
        earliest_date = today_eastern
        earliest_time = earliest_time or "11:30"
    requested_date, requested_time = _split_foc_value(values.get("requestedFocDate"))
    # Bandwidth portal behavior: default to the current scheduling floor only
    # when no later date has already been selected.
    if not requested_date or requested_date < earliest_date:
        requested_date = earliest_date
    if not requested_time:
        requested_time = earliest_time or "11:30"
    values["requestedFocDate"] = requested_date
    values["requestedFocTime"] = requested_time
    if "useEarliest" not in values:
        values["useEarliest"] = True
    draft = save_draft(db, request.state.user, values, draft_id=draft.id, status="ready_to_schedule")
    profile = _port_profile(values.get("portType"), values.get("phoneNumberType"))
    return render(request, "port_schedule.html", values=values, draft=draft,
                  earliest_date=earliest_date, earliest_time=earliest_time or "11:30",
                  earliest_display=_friendly_eastern(values.get("earliestEstimate")), profile=profile)


@router.post("/new/submit")
async def submit_port(
    request: Request,
    loaAuthorizingPerson: str = Form(...),
    subAccountId: int = Form(...),
    locationId: int = Form(...),
    phoneNumbers: str = Form(...),
    billingTelephoneNumber: str = Form(""),
    accountType: str = Form("BUSINESS"),
    customerName: str = Form(""),
    accountNumber: str = Form(""),
    accountPin: str = Form(""),
    streetNumber: str = Form(""),
    streetName: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    zip: str = Form(""),
    zip4: str = Form(""),
    losingCarrierName: str = Form(""),
    requestedFocDate: str = Form(""),
    requestedFocTime: str = Form(""),
    earliestEstimate: str = Form(""),
    useEarliest: str = Form("true"),
    portType: str = Form(""),
    phoneNumberType: str = Form(""),
    portingAllNumbers: str | None = Form(None),
    newBillingTelephoneNumber: str = Form(""),
    draft_id: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create the Bandwidth order only after the explicit review step."""
    require_bandwidth_site(request, subAccountId)
    values = {
        "loaAuthorizingPerson": loaAuthorizingPerson,
        "subAccountId": subAccountId,
        "locationId": locationId,
        "phoneNumbers": phoneNumbers,
        "billingTelephoneNumber": billingTelephoneNumber,
        "accountType": accountType,
        "customerName": customerName,
        "accountNumber": accountNumber,
        "accountPin": accountPin,
        "streetNumber": streetNumber,
        "streetName": streetName,
        "address2": address2,
        "city": city,
        "state": state,
        "zip": zip,
        "zip4": zip4,
        "losingCarrierName": losingCarrierName,
        "requestedFocDate": requestedFocDate,
        "requestedFocTime": requestedFocTime,
        "earliestEstimate": earliestEstimate,
        "useEarliest": _use_earliest_selected(useEarliest),
        "portType": portType,
        "phoneNumberType": phoneNumberType,
        "portingAllNumbers": portingAllNumbers is not None,
        "newBillingTelephoneNumber": newBillingTelephoneNumber,
    }
    draft = save_draft(db, request.state.user, values, draft_id=draft_id or None, status="ready_to_submit")
    values, verification = await _refresh_draft_portability(db, request, draft, values, reason="submission")
    if verification["status"] == "failed":
        sites, locations_by_site = await _port_form_options(request)
        return render(
            request, "port_new.html", sites=sites, locations_by_site=locations_by_site,
            phoneNumbers=phoneNumbers, error=None, verification=verification,
            form_values=values, draft=draft,
        )
    if verification["status"] == "changed":
        # Portability is refreshed immediately before submission. If Bandwidth
        # moved the earliest estimate, return to the final scheduling step so
        # the user never submits a now-invalid/stale date.
        earliest_date, earliest_time = _split_foc_value(values.get("earliestEstimate"))
        chosen_date, chosen_time = _split_foc_value(values.get("requestedFocDate"))
        if not chosen_date or (earliest_date and chosen_date < earliest_date):
            values["useEarliest"] = True
            values["requestedFocDate"] = earliest_date
            values["requestedFocTime"] = earliest_time or "11:30"
        draft = save_draft(db, request.state.user, values, draft_id=draft.id, status="ready_to_schedule")
        return render(
            request, "port_schedule.html", values=values, draft=draft,
            earliest_date=earliest_date, earliest_time=earliest_time or "11:30",
            earliest_display=_friendly_eastern(values.get("earliestEstimate")),
            profile=_port_profile(values.get("portType"), values.get("phoneNumberType")),
            verification=verification,
        )

    # Exception resubmits must never reuse a stale FOC.  Bandwidth rejects an
    # existing-order PUT when RequestedFocDate is in the past (7208).  Refresh
    # the live scheduling floor above, then force the user back through the
    # final schedule step whenever the saved request is now stale.
    existing_order_for_resubmit = bool(str(draft.bandwidth_order_id or "").strip())
    if existing_order_for_resubmit:
        requested_date, requested_time = _split_foc_value(values.get("requestedFocDate"))
        earliest_date, earliest_time = _split_foc_value(values.get("earliestEstimate"))
        today_eastern = datetime.now(EASTERN).date().isoformat()
        scheduling_floor = max([d for d in (earliest_date, today_eastern) if d])
        if not requested_date or requested_date < scheduling_floor:
            values["useEarliest"] = True
            values["requestedFocDate"] = scheduling_floor
            values["requestedFocTime"] = earliest_time or requested_time or "11:30"
            if not earliest_date or earliest_date < scheduling_floor:
                values["earliestEstimate"] = _bandwidth_utc_timestamp(
                    scheduling_floor, values["requestedFocTime"]
                )
            draft = save_draft(db, request.state.user, values, draft_id=draft.id, status="ready_to_schedule")
            add_timeline_event(
                db, draft, "schedule_refresh_required", "Activation date refreshed",
                f"The prior requested activation date is no longer valid. Select a date on or after {scheduling_floor} before resubmitting.",
                severity="warning", user_id=request.state.user.id,
            )
            db.commit()
            return render(
                request, "port_schedule.html", values=values, draft=draft,
                earliest_date=scheduling_floor, earliest_time=values["requestedFocTime"],
                earliest_display=_friendly_eastern(values.get("earliestEstimate")),
                profile=_port_profile(values.get("portType"), values.get("phoneNumberType")),
                verification={
                    "status": "changed",
                    "message": "The previous requested activation date is no longer valid. Choose the refreshed date or a later date before resubmitting.",
                },
            )

    validation_error = _validate_btn_workflow(values) or _validate_foc_selection(values)
    if validation_error:
        sites, locations_by_site = await _port_form_options(request)
        return render(
            request, "port_new.html", sites=sites,
            locations_by_site=locations_by_site, phoneNumbers=phoneNumbers,
            error={"message": validation_error, "payload": {}}, form_values=values, draft=draft,
        )

    payload = _build_port_payload(values)

    # Final provider-boundary guard for exception/correction resubmits.  Older
    # drafts can carry a RequestedFocDate that predates the current OnePort
    # estimate even after the scheduling UI has been refreshed.  Never allow
    # that stale timestamp to reach Bandwidth: when the user is using the
    # portal-style "earliest available" choice, replace it with the freshly
    # verified OnePort estimate immediately before the PUT.  This specifically
    # prevents Bandwidth 7208 (requested FOC date cannot be in the past).
    existing_order_for_payload = bool(str(draft.bandwidth_order_id or "").strip())
    if existing_order_for_payload:
        requested_dt = _parse_estimate_datetime(payload.get("requestedFocDate"))
        earliest_dt = _parse_estimate_datetime(values.get("earliestEstimate"))
        now_utc = datetime.now(timezone.utc)
        use_earliest_now = _use_earliest_selected(values.get("useEarliest"))

        stale_requested = requested_dt is None or requested_dt <= now_utc
        if earliest_dt is not None and requested_dt is not None and requested_dt < earliest_dt:
            stale_requested = True

        if stale_requested:
            if use_earliest_now and earliest_dt is not None and earliest_dt > now_utc:
                corrected_foc = earliest_dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                payload["requestedFocDate"] = corrected_foc
                corrected_local = earliest_dt.astimezone(EASTERN)
                values["requestedFocDate"] = corrected_local.date().isoformat()
                values["requestedFocTime"] = corrected_local.strftime("%H:%M")
                draft = save_draft(db, request.state.user, values, draft_id=draft.id, status="ready_to_submit")
                add_timeline_event(
                    db, draft, "requested_foc_refreshed", "Requested activation refreshed",
                    f"The prior requested activation was stale. NOP replaced it with the current earliest available activation: {_friendly_eastern(corrected_foc)}.",
                    severity="info", user_id=request.state.user.id,
                )
                db.commit()
                logger.info("Replaced stale existing-order requested FOC with refreshed earliest estimate: %s", corrected_foc)
            else:
                # A user-selected date must never be silently moved. Return to
                # scheduling so the correction can be explicitly rescheduled.
                earliest_date, earliest_time = _split_foc_value(values.get("earliestEstimate"))
                scheduling_floor = earliest_date or datetime.now(EASTERN).date().isoformat()
                values["requestedFocDate"] = scheduling_floor
                values["requestedFocTime"] = earliest_time or values.get("requestedFocTime") or "11:30"
                draft = save_draft(db, request.state.user, values, draft_id=draft.id, status="ready_to_schedule")
                add_timeline_event(
                    db, draft, "schedule_refresh_required", "Activation date must be refreshed",
                    "The previously requested activation date is no longer valid. Select the refreshed date or a later date before resubmitting.",
                    severity="warning", user_id=request.state.user.id,
                )
                db.commit()
                return render(
                    request, "port_schedule.html", values=values, draft=draft,
                    earliest_date=scheduling_floor, earliest_time=values["requestedFocTime"],
                    earliest_display=_friendly_eastern(values.get("earliestEstimate")),
                    profile=_port_profile(values.get("portType"), values.get("phoneNumberType")),
                    verification={
                        "status": "changed",
                        "message": "The previous requested activation date is no longer valid. Choose the refreshed date or a later date before resubmitting.",
                    },
                )

    logger.info(
        "Submitting Bandwidth port: portType=%r phoneNumberType=%r requestedFocDate=%r triggered=%r",
        values.get("portType"),
        values.get("phoneNumberType"),
        payload.get("requestedFocDate"),
        payload.get("triggered", "omitted"),
    )
    try:
        # Bandwidth creates a provider-side draft first.  A separate PUT with
        # ProcessingStatus=SUBMITTED is required before the order enters the
        # active porting workflow.
        # Corrections/resubmissions must update the existing Bandwidth order,
        # not create a duplicate order. A prior provider-side DRAFT is also
        # recoverable for failed first submissions.
        existing_order_id = str(draft.bandwidth_order_id or "").strip()
        existing_payload: dict[str, Any] = {}
        if not existing_order_id:
            existing_order_id, existing_payload = _provider_draft_from_attempts(draft)
        is_existing_active_order = False
        if existing_order_id:
            order_id = existing_order_id
            create_result = {"reusedProviderOrder": order_id}
            # Always use the newly edited payload for a correction. The older
            # request payload may contain the TNs that the user just changed.
            submit_payload = dict(payload)
            # Existing submitted/exception orders are updated in place.  Do not
            # send ProcessingStatus for those orders: Bandwidth owns the state of
            # AUTOMATED ports and rejects attempts to modify it (7367).
            try:
                current_before_update = _unwrap_port_detail(await bw.porting.get(order_id))
                current_provider_status = str(
                    _get_ci(current_before_update, "processingStatus", "ProcessingStatus", "status") or ""
                ).strip().upper()
            except Exception:
                current_provider_status = str(draft.bandwidth_status or "").strip().upper()
            is_existing_active_order = current_provider_status not in {"", "DRAFT"}
            if is_existing_active_order:
                submit_payload.pop("processingStatus", None)
                submit_payload.pop("ProcessingStatus", None)
                submit_result = await bw.porting.update(order_id, submit_payload)
            else:
                submit_result = await bw.porting.submit_draft(order_id, submit_payload)
        else:
            create_result = await bw.porting.create(payload)
            order_id, create_status = _port_order_response_details(create_result)
            if not order_id:
                raise RuntimeError("The port-in API accepted the request but did not return an order id.")
            submit_payload = payload
            record_attempt(db, draft, payload, success=True, response=create_result)
            submit_result = await bw.porting.submit_draft(order_id, submit_payload)

        final_order_id, final_status = _port_order_response_details(submit_result)
        order_id = final_order_id or order_id

        # Some update responses are acknowledgement-only. Fetch the order so
        # the local status reflects the provider's actual current state.
        if not final_status or final_status == "DRAFT" or is_existing_active_order:
            current_result = await bw.porting.get(order_id)
            _, current_status = _port_order_response_details(current_result)
            if current_status:
                final_status = current_status
            submit_result = {"submitResponse": submit_result, "currentOrder": current_result}

        # A newly-created provider draft must leave DRAFT/EXCEPTION to count as
        # an initial submission.  An existing exception correction is different:
        # a successful PUT can remain EXCEPTION briefly while Bandwidth reprocesses
        # it, so do not turn that accepted correction into a false NOP failure.
        if not is_existing_active_order and final_status in {"DRAFT", "EXCEPTION"}:
            raise RuntimeError(f"Port order {order_id} remains in provider status {final_status} after submission.")

        # Provider acceptance is the transaction boundary. Persist the provider
        # order id/status first, then treat attempts, timeline entries and email
        # notifications as best-effort local follow-up work. A local post-submit
        # failure must never turn an accepted Bandwidth submission into a browser
        # 500 that encourages an accidental duplicate retry.
        draft.status = "submitted"
        draft.bandwidth_order_id = str(order_id)
        draft.bandwidth_status = final_status or "SUBMITTED"
        draft.last_error_code = ""
        draft.last_error_message = ""
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "Bandwidth accepted port %s, but NOP could not persist the provider result",
                order_id,
            )
            return RedirectResponse(
                f"/ports/{order_id}?notice=Provider+accepted+the+port%2C+but+NOP+could+not+save+all+local+submission+details.",
                303,
            )

        try:
            # Freeze the notification recipient at submission time so future
            # provider events continue going to the NOP user who submitted it.
            draft.submitted_by_user_id = request.state.user.id
            draft.notification_email = str(getattr(request.state.user, "email", "") or "").strip()
            draft.notifications_enabled = True
            draft.notification_state_json = json.dumps({
                "last_status": draft.bandwidth_status,
                "submitted_email_sent": True,
            }, sort_keys=True)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Port %s was accepted, but notification ownership could not be persisted", order_id)

        try:
            record_attempt(db, draft, submit_payload, success=True, response=submit_result)
            add_timeline_event(
                db, draft, "submitted",
                "Port correction submitted" if is_existing_active_order else "Port request submitted",
                (
                    f"Correction for order {order_id} was accepted; current provider status is {final_status or 'SUBMITTED'}."
                    if is_existing_active_order
                    else f"Order {order_id} entered the porting workflow with status {final_status or 'SUBMITTED'}."
                ),
                severity="success", user_id=request.state.user.id,
            )
        except Exception:
            db.rollback()
            logger.exception("Port %s was accepted, but NOP post-submit audit logging failed", order_id)

        # Submission email is ancillary. Template/SMTP failures are logged but
        # must never break the successful redirect after Bandwidth acceptance.
        try:
            order_url = f"{str(request.base_url).rstrip('/')}/ports/{order_id}"
            email_body = render_email_template(
                "port_submitted.html",
                nti_reference=draft.nti_reference,
                customer_name=draft.customer_name or "Not entered",
                order_id=order_id,
                status=draft.bandwidth_status,
                phone_numbers=", ".join(_numbers(str(submit_payload.get("phoneNumbers") or ""))) or draft.billing_telephone_number,
                provider_note="No provider note was included.",
                order_url=order_url,
            )
            send_port_email(
                f"Port Request Submitted - {draft.nti_reference}",
                email_body,
                [draft.notification_email],
            )
        except Exception:
            logger.exception("Port %s was accepted, but the submission email could not be prepared/sent", order_id)

        return RedirectResponse(f"/ports/{order_id}", 303)
    except BandwidthAPIError as exc:
        friendly = translate_bandwidth_error(exc, operation="port_submit")
        diagnostic = exc.diagnostic or {}
        code = friendly.get("error_code") or friendly.get("status_code") or ""
        message = friendly.get("message") or "The request could not be accepted."
        draft.status = "submission_failed"
        draft.last_error_code = str(code or "")
        draft.last_error_message = str(message)
        record_attempt(
            db, draft, payload, success=False, response=diagnostic,
            error={"code": code, "message": message},
        )
        add_timeline_event(db, draft, "submission_failed", "Submission failed", str(message), severity="danger", user_id=request.state.user.id)
        logger.warning(
            "Port submission rejected: status=%r code=%r detail=%r diagnostic=%r",
            exc.status_code, code, friendly.get("provider_message"), diagnostic,
        )
        db.commit()
        return RedirectResponse(f"/ports/drafts/{draft.id}", 303)


def _find_order_id_in_webhook(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("orderId", "OrderId", "order_id", "id"):
            candidate = _get_ci(value, key)
            if candidate not in (None, "") and key.casefold() != "id" or (key.casefold() == "id" and "order" in " ".join(str(k).casefold() for k in value.keys())):
                text = str(candidate or "").strip()
                if text:
                    return text
        for nested in value.values():
            found = _find_order_id_in_webhook(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_order_id_in_webhook(nested)
            if found:
                return found
    return ""


@router.post("/webhooks/bandwidth")
async def bandwidth_port_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive Bandwidth port notifications and refresh provider-authoritative status.

    Configure BANDWIDTH_PORT_WEBHOOK_TOKEN and include it as either the `token`
    query parameter or X-Webhook-Token header in the callback configuration.
    """
    expected = str(get_settings().bandwidth_port_webhook_token or "").strip()
    supplied = str(request.query_params.get("token") or request.headers.get("X-Webhook-Token") or "").strip()
    if not expected:
        return JSONResponse({"detail": "Port webhook token is not configured."}, status_code=503)
    if supplied != expected:
        return JSONResponse({"detail": "Invalid webhook token."}, status_code=401)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    order_id = _find_order_id_in_webhook(payload)
    if not order_id:
        return JSONResponse({"detail": "No Bandwidth order id was found in the webhook payload."}, status_code=400)
    try:
        live = _unwrap_port_detail(await bw.porting.get(order_id))
        sent = _process_port_notification_safely(
            db, live,
            order_url=f"{str(request.base_url).rstrip('/')}/ports/{order_id}",
        )
        db.commit()
        return JSONResponse({"accepted": True, "order_id": order_id, "notifications_sent": sent}, status_code=202)
    except BandwidthAPIError as exc:
        db.rollback()
        return JSONResponse({"accepted": False, "order_id": order_id, "provider_error": exc.diagnostic}, status_code=502)


@router.get("/{order_id}", response_class=HTMLResponse)
async def port_detail(request: Request, order_id: str, db: Session = Depends(get_db)):
    try:
        raw_order = await bw.porting.get(order_id)
        order = _unwrap_port_detail(raw_order)
        require_bandwidth_site(request, order.get("subAccountId"))
        order["requestedFocDateDisplay"] = _friendly_eastern(order.get("requestedFocDate"))
        order["actualFocDateDisplay"] = _friendly_eastern(order.get("actualFocDate"))
        order["earliestEstimateDisplay"] = _friendly_eastern(order.get("earliestEstimate"))
        # Provider-authoritative status/note changes are de-duplicated and sent
        # to the email address frozen when the order was submitted.
        sent_events = _process_port_notification_safely(
            db, order,
            order_url=f"{str(request.base_url).rstrip('/')}/ports/{order_id}",
        )
        if sent_events:
            db.commit()
        tracked_draft = db.scalar(select(PortDraft).where(PortDraft.bandwidth_order_id == str(order_id)))
        return render(
            request,
            "port_detail.html",
            order=order,
            order_id=order_id,
            error=None,
            tracked_draft=tracked_draft,
        )
    except BandwidthAPIError as exc:
        return render(
            request,
            "port_detail.html",
            order={},
            order_id=order_id,
            error=exc.diagnostic,
            tracked_draft=None,
        )


@router.get("/{order_id}/numbers/edit", response_class=HTMLResponse)
async def edit_port_numbers_page(request: Request, order_id: str):
    try:
        order = _unwrap_port_detail(await bw.porting.get(order_id))
        require_bandwidth_site(request, order.get("subAccountId"))
        return render(
            request,
            "port_edit_numbers.html",
            order=order,
            order_id=order_id,
            error=None,
            add_numbers="",
            remove_numbers="",
        )
    except BandwidthAPIError as exc:
        return render(
            request, "port_edit_numbers.html", order={}, order_id=order_id,
            error=exc.diagnostic, add_numbers="", remove_numbers="",
        )


@router.post("/{order_id}/numbers/edit", response_class=HTMLResponse)
async def edit_port_numbers_submit(
    request: Request,
    order_id: str,
    add_numbers: str = Form(""),
    remove_numbers: str = Form(""),
):
    try:
        order = _unwrap_port_detail(await bw.porting.get(order_id))
        require_bandwidth_site(request, order.get("subAccountId"))
        current = list(dict.fromkeys(_normalize_e164(str(n)) for n in (order.get("phoneNumbers") or [])))
        additions = _numbers(add_numbers) if add_numbers.strip() else []
        removals = set(_numbers(remove_numbers)) if remove_numbers.strip() else set()
        target = [n for n in current if n not in removals]
        for number in additions:
            if number not in target:
                target.append(number)
        if not target:
            raise ValueError("A port order must contain at least one telephone number.")
        if target == current:
            return RedirectResponse(f"/ports/{order_id}", 303)

        # For an existing port order, Bandwidth is the authority on whether the
        # revised TN set may remain on that order.  The portability checker can
        # legitimately return more than one grouping for a submitted order
        # (for example when estimates or carrier metadata differ), so do not
        # reject the edit locally solely because summary grouping count != 1.
        #
        # We still run the check to catch explicitly non-portable TNs and to
        # retain useful diagnostics, but the actual PUT is allowed to decide
        # whether the existing order can accept the revised list.
        portability_raw = await bw.porting.check_portability(target)
        portability = _portability_summary(portability_raw)
        blocking_nonportable = _blocking_nonportable_for_existing_order(portability, current)
        if blocking_nonportable:
            filtered_portability = dict(portability)
            filtered_portability["nonportable"] = blocking_nonportable
            return render(
                request, "port_edit_numbers.html", order=order, order_id=order_id,
                error={"message": "One or more new or changed telephone numbers are not portable. Remove or correct those numbers and validate again.", "payload": filtered_portability},
                add_numbers=add_numbers, remove_numbers=remove_numbers,
            )

        try:
            await bw.porting.update(order_id, {"phoneNumbers": target})
        except BandwidthAPIError as exc:
            # Surface the provider's real restriction (for example a submitted
            # port type that no longer allows TN edits) rather than replacing it
            # with NOP's portability grouping heuristic.
            return render(
                request, "port_edit_numbers.html", order=order, order_id=order_id,
                error=exc.diagnostic, add_numbers=add_numbers, remove_numbers=remove_numbers,
            )

        refreshed = _unwrap_port_detail(await bw.porting.get(order_id))
        return RedirectResponse(f"/ports/{order_id}?notice=Telephone+numbers+updated", 303)
    except ValueError as exc:
        try:
            order
        except NameError:
            order = {}
        return render(
            request, "port_edit_numbers.html", order=order, order_id=order_id,
            error={"message": str(exc), "payload": {}}, add_numbers=add_numbers,
            remove_numbers=remove_numbers,
        )
    except BandwidthAPIError as exc:
        try:
            order
        except NameError:
            order = {}
        return render(
            request, "port_edit_numbers.html", order=order, order_id=order_id,
            error=exc.diagnostic, add_numbers=add_numbers, remove_numbers=remove_numbers,
        )


@router.get("/{order_id}/schedule/edit", response_class=HTMLResponse)
async def edit_port_schedule_page(request: Request, order_id: str):
    try:
        order = _unwrap_port_detail(await bw.porting.get(order_id))
        require_bandwidth_site(request, order.get("subAccountId"))
        values = _live_order_values(order, {})
        values, portability = await _latest_portability_for_edit(values)
        current_date, current_time = _split_foc_value(order.get("requestedFocDate"))
        port_type = _get_ci(order, "portType", "PortType") or values.get("portType") or ""
        number_type = _get_ci(order, "phoneNumberType", "PhoneNumberType") or values.get("phoneNumberType") or ""
        triggered = _provider_bool(_get_ci(order, "triggered", "Triggered"))
        profile = _port_profile(port_type, number_type)
        time_editable = profile["kind"] == "automated_wireless" or triggered
        return render(
            request, "port_edit_schedule.html", order=order, order_id=order_id,
            error=None, requested_date=current_date, requested_time=current_time or "11:30",
            earliest_estimate=values.get("earliestEstimate") or "",
            current_requested_display=_friendly_eastern(order.get("requestedFocDate")),
            current_foc_display=_friendly_eastern(order.get("actualFocDate")),
            earliest_display=_friendly_eastern(values.get("earliestEstimate")),
            profile=profile, time_editable=time_editable, triggered=triggered,
        )
    except BandwidthAPIError as exc:
        return render(
            request, "port_edit_schedule.html", order={}, order_id=order_id,
            error=exc.diagnostic, requested_date="", requested_time="11:30",
            earliest_estimate="", profile={"label": "Unknown"}, time_editable=False,
            triggered=False,
        )


@router.post("/{order_id}/schedule/edit", response_class=HTMLResponse)
async def edit_port_schedule_submit(
    request: Request,
    order_id: str,
    requested_date: str = Form(...),
    requested_time: str = Form("11:30"),
):
    try:
        order = _unwrap_port_detail(await bw.porting.get(order_id))
        require_bandwidth_site(request, order.get("subAccountId"))
        port_type = _get_ci(order, "portType", "PortType") or ""
        number_type = _get_ci(order, "phoneNumberType", "PhoneNumberType") or ""
        triggered = _provider_bool(_get_ci(order, "triggered", "Triggered"))
        profile = _port_profile(port_type, number_type)

        current_date, current_time = _split_foc_value(order.get("requestedFocDate"))
        values = {"phoneNumbers": " ".join(order.get("phoneNumbers") or [])}
        values, _ = await _latest_portability_for_edit(values)
        earliest_date, _ = _split_foc_value(values.get("earliestEstimate"))
        if earliest_date and requested_date < earliest_date:
            raise ValueError(f"Requested activation date cannot be earlier than Bandwidth's current earliest available date ({earliest_date}).")

        # All date/time controls are Eastern. For a locked provider time, keep
        # the same Eastern clock time while changing only the calendar date.
        effective_time = requested_time if time_editable else (current_time or requested_time or "11:30")
        requested_foc, requested_triggered = _build_requested_foc(
            requested_date, effective_time, port_type, number_type
        )
        payload = {"requestedFocDate": requested_foc}
        if triggered or requested_triggered is True:
            payload["triggered"] = True

        await bw.porting.update(order_id, payload)
        return RedirectResponse(f"/ports/{order_id}?notice=Activation+date+updated", 303)
    except ValueError as exc:
        try:
            order
        except NameError:
            order = {}
        current_date, current_time = _split_foc_value((order or {}).get("requestedFocDate"))
        return render(
            request, "port_edit_schedule.html", order=order, order_id=order_id,
            error={"message": str(exc), "payload": {}}, requested_date=requested_date,
            requested_time=requested_time or current_time or "11:30", earliest_estimate="",
            profile=_port_profile(_get_ci(order, "portType", "PortType"), _get_ci(order, "phoneNumberType", "PhoneNumberType")),
            time_editable=False, triggered=False,
        )
    except BandwidthAPIError as exc:
        try:
            order
        except NameError:
            order = {}
        current_date, current_time = _split_foc_value((order or {}).get("requestedFocDate"))
        return render(
            request, "port_edit_schedule.html", order=order, order_id=order_id,
            error=exc.diagnostic, requested_date=requested_date or current_date,
            requested_time=requested_time or current_time or "11:30", earliest_estimate="",
            profile=_port_profile(_get_ci(order, "portType", "PortType"), _get_ci(order, "phoneNumberType", "PhoneNumberType")),
            time_editable=False, triggered=False,
        )


@router.get("/{order_id}/correct")
async def correct_port_order(request: Request, order_id: str, db: Session = Depends(get_db)):
    user = request.state.user
    draft = db.scalar(select(PortDraft).where(
        PortDraft.organization_id == user.organization_id,
        PortDraft.bandwidth_order_id == order_id,
    ))
    if not draft:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No local correction record was found for this order.")
    try:
        live = _unwrap_port_detail(await bw.porting.get(order_id))
        require_bandwidth_site(request, live.get("subAccountId"))
        values = _live_order_values(live, load_values(draft))
        values, _ = await _latest_portability_for_edit(values)
        draft.payload_json = json.dumps(values, default=str, separators=(",", ":"))
        draft.billing_telephone_number = str(values.get("billingTelephoneNumber") or draft.billing_telephone_number or "")
        draft.losing_carrier_name = str(values.get("losingCarrierName") or draft.losing_carrier_name or "")
    except BandwidthAPIError:
        pass
    draft.status = "requires_attention"
    db.commit()
    return RedirectResponse(f"/ports/drafts/{draft.id}/edit", 303)


@router.post("/{order_id}/cancel")
async def cancel_port(request: Request, order_id: str):
    order = _unwrap_port_detail(await bw.porting.get(order_id))
    require_bandwidth_site(request, order.get("subAccountId"))
    await bw.porting.cancel(order_id)
    return RedirectResponse(f"/ports/{order_id}", 303)
