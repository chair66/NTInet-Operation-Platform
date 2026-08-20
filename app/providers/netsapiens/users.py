from __future__ import annotations

from typing import Any
import json
import logging
import re

from app.config import get_settings
from urllib.parse import quote

from .client import NetSapiensClient

logger = logging.getLogger(__name__)


def _yes(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled", "active"}


def _voicemail_notification_state(raw: dict[str, Any], fallback_email: str = "") -> dict[str, Any]:
    """Normalize NetSapiens v2 and legacy voicemail notification fields."""
    v2_enabled = _deep_value(raw, "email-send-alert-new-voicemail-enabled", default=None)
    behavior = str(_deep_value(
        raw,
        "email-send-alert-new-voicemail-behavior",
        "vmail_notify_enabled",
        "voicemail-notify-enabled",
        default="",
    ) or "").strip().lower()
    recipient = str(_deep_value(
        raw,
        "email-send-alert-new-voicemail-cc-list-csv",
        "vmail_notify",
        "voicemail-notify",
        default=fallback_email,
    ) or "").strip()

    enabled = _yes(v2_enabled, False) if v2_enabled is not None else behavior not in {
        "", "0", "no", "false", "off", "disabled"
    }
    email_type = "attachment" if behavior.startswith("att") else "notification"
    if behavior.endswith("trash"):
        after_action = "trash"
    elif behavior.endswith("save"):
        after_action = "saved"
    else:
        after_action = "new"
    return {
        "enabled": enabled,
        "recipient": recipient,
        "email_type": email_type,
        "after_action": after_action,
        "token": behavior,
    }


def _voicemail_notification_token(enabled: bool, email_type: str, after_action: str) -> str:
    if not enabled:
        return ""
    if email_type == "notification":
        return "yes"
    return {"new": "attnew", "saved": "attsave", "trash": "atttrash"}.get(after_action, "atttrash")


def _rows(result: Any) -> list[dict[str, Any]]:
    """Normalize the common NetSapiens collection response envelopes."""
    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]
    if isinstance(result, dict):
        for key in ("data", "users", "items", "results", "records"):
            value = result.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        if any(key in result for key in ("user", "username", "extension", "login")):
            return [result]
    return []


def _value(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default



def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _deep_value(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    """Find a value across nested API objects using tolerant key matching."""
    wanted = {_normalized_key(key) for key in keys}
    queue: list[Any] = [row]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            for key, value in current.items():
                if _normalized_key(key) in wanted and value not in (None, ""):
                    return value
            queue.extend(value for value in current.values() if isinstance(value, (dict, list)))
        elif isinstance(current, list):
            queue.extend(value for value in current if isinstance(value, (dict, list)))
    return default


def _redacted_debug_payload(value: Any) -> Any:
    """Redact secrets while keeping profile field names visible during development."""
    sensitive = {"password", "passwd", "pin", "token", "secret", "authorization", "apikey", "api_key"}
    if isinstance(value, dict):
        return {
            key: ("***REDACTED***" if _normalized_key(key) in {_normalized_key(k) for k in sensitive} else _redacted_debug_payload(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redacted_debug_payload(item) for item in value]
    return value


def _enabled(row: dict[str, Any]) -> bool | None:
    value = _value(row, "enabled", "active", "status", "user_enabled", default=None)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"yes", "true", "1", "active", "enabled", "registered"}:
        return True
    if normalized in {"no", "false", "0", "disabled", "inactive", "suspended"}:
        return False
    return None


class NetSapiensUsers:
    """Live DigiCloud user inventory operations."""

    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    def list(self, domain: str) -> list[dict[str, Any]]:
        result = self.client.request(
            "GET",
            f"/domains/{quote(domain, safe='')}/users",
            params={"limit": 10000},
        )
        normalized: list[dict[str, Any]] = []
        for raw in _rows(result):
            username = str(_value(raw, "user", "username", "login", "extension")).strip()
            first_name = str(_value(raw, "first_name", "firstname", "first-name", "given_name")).strip()
            last_name = str(_value(raw, "last_name", "lastname", "last-name", "surname")).strip()
            caller_id_name = str(_value(raw, "caller-id-name", "caller_id_name", "callerid-name", "callerid_name")).strip()
            full_name = str(_value(raw, "name", "display_name", "display-name")).strip()
            if not full_name:
                full_name = " ".join(part for part in (first_name, last_name) if part).strip()
            if not full_name and caller_id_name:
                full_name = caller_id_name
            if not full_name:
                full_name = username or "Unnamed User"

            device_value = _value(raw, "device_count", "devices_count", "phone_count", default=None)
            try:
                device_count = int(device_value) if device_value not in (None, "") else None
            except (TypeError, ValueError):
                device_count = None

            scope = str(_value(
                raw,
                "scope", "user_scope", "user-scope", "scope_name", "scope-name",
                "user_type", "user-type", "type",
            )).strip()

            normalized.append({
                "username": username,
                "extension": str(_value(raw, "extension", "user", "username", "login")).strip(),
                "first_name": first_name,
                "last_name": last_name,
                "name": full_name,
                "email": str(_value(raw, "email", "email_address", "email-address")).strip(),
                "department": str(_value(raw, "department", "department_name", "department-name")).strip(),
                "scope": scope,
                "enabled": _enabled(raw),
                "device_count": device_count,
                "raw": raw,
            })

        domain_normalized = domain.strip().lower().rstrip(".")
        for row in normalized:
            row["hidden_reason"] = self.hidden_reason(row, domain_normalized)
            row["hidden"] = row["hidden_reason"] is not None

        return sorted(normalized, key=lambda row: (row["name"].lower(), row["extension"]))

    @staticmethod
    def hidden_reason(row: dict[str, Any], domain: str) -> str | None:
        """Return the default NOP visibility reason for internal DigiCloud users."""
        scope = str(row.get("scope") or "").strip().lower()
        if scope == "ndp" or "ndp" in {part.strip() for part in scope.replace("/", " ").split()}:
            return "NDP Scope"
        if scope in {"system", "sys", "system user", "system-user"}:
            return "System Scope"

        identities = {
            str(row.get("username") or "").strip().lower().rstrip("."),
            str(row.get("extension") or "").strip().lower().rstrip("."),
        }
        local_part = domain.split(".", 1)[0] if domain else ""
        domain_aliases = {domain, f"{domain}@{domain}", local_part}
        if domain and identities.intersection(domain_aliases):
            return "Domain User"

        raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        raw_domain = str(_value(raw, "domain", "domain_name", "domain-name")).strip().lower().rstrip(".")
        raw_user = str(_value(raw, "user", "username", "login", "extension")).strip().lower().rstrip(".")
        if domain and raw_domain == domain and raw_user in {domain, local_part}:
            return "Domain User"
        return None

    def get(self, domain: str, username: str) -> dict[str, Any]:
        """Retrieve and normalize one live DigiCloud user profile.

        DigiCloud installations sometimes return a reduced record from the
        single-user endpoint.  Merge the matching collection record so fields
        such as customer name are retained when they only exist in the list.
        """
        result = self.client.request(
            "GET",
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}",
        )

        settings = get_settings()
        if settings.app_env.strip().lower() in {"development", "dev", "local"}:
            logger.info(
                "DigiCloud raw user profile for %s in %s:\n%s",
                username,
                domain,
                json.dumps(_redacted_debug_payload(result), indent=2, default=str),
            )

        raw: dict[str, Any] = {}
        if isinstance(result, dict):
            for key in ("data", "user", "item", "record", "subscriber", "profile"):
                value = result.get(key)
                if isinstance(value, dict):
                    raw = value
                    break
            if not raw:
                raw = result
        elif isinstance(result, list) and result and isinstance(result[0], dict):
            raw = result[0]

        # Merge the matching row from the collection endpoint.  Prefer values
        # returned by the detail endpoint, but fill blanks from the list row.
        list_match: dict[str, Any] = {}
        try:
            wanted = username.strip().lower()
            for item in self.list(domain):
                identities = {
                    str(item.get("username") or "").strip().lower(),
                    str(item.get("extension") or "").strip().lower(),
                }
                if wanted in identities:
                    list_match = item
                    break
        except Exception as exc:  # Detail editing must still work if list enrichment fails.
            logger.debug("Unable to enrich DigiCloud profile from user list: %s", exc)

        first_name = str(_deep_value(
            raw, "first_name", "firstname", "first-name", "given_name", "given-name",
            "name_first", "name-first", "first",
            default=list_match.get("first_name", ""),
        )).strip()
        last_name = str(_deep_value(
            raw, "last_name", "lastname", "last-name", "surname", "family_name",
            "family-name", "name_last", "name-last", "last",
        )).strip()
        caller_id_name = str(_deep_value(
            raw, "caller_id_name", "caller-id-name", "callerid_name", "callerid-name",
            "cid_name", "cid-name",
        )).strip()
        display_name = str(_deep_value(
            raw, "display_name", "display-name", "full_name", "full-name",
            "subscriber_name", "subscriber-name", "name",
            default="",
        )).strip()

        # A number/username is an identifier, not a person's name. Some
        # DigiCloud responses omit separate first/last-name fields and only
        # provide the customer's name in caller-id-name.
        identity_values = {
            str(username or "").strip().lower(),
            str(list_match.get("username") or "").strip().lower(),
            str(list_match.get("extension") or "").strip().lower(),
        }
        if display_name.strip().lower() in identity_values or display_name.replace("+", "").isdigit():
            display_name = ""
        if not display_name and caller_id_name:
            display_name = caller_id_name
        if display_name and not first_name and not last_name:
            parts = display_name.split(None, 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        resolved_username = str(_deep_value(
            raw, "user", "username", "login", "extension",
            default=list_match.get("username") or username,
        )).strip()
        resolved_extension = str(_deep_value(
            raw, "extension", "user", "username", "login",
            default=list_match.get("extension") or username,
        )).strip()

        emergency_caller_id = str(_deep_value(
            raw,
            "caller-id-number-emergency", "caller_id_number_emergency",
            "emergency_caller_id", "emergency-caller-id",
            "emergency_caller_id_number", "emergency-caller-id-number",
            "emergency_cid", "emergency-cid",
            "emergency_number", "emergency-number",
            "e911_caller_id", "e911-caller-id", "e911_caller_id_number",
            "911_caller_id", "911-caller-id", "911_caller_id_number",
        )).strip()
        emergency_caller_id_configured = bool(emergency_caller_id)
        # Residential DigiCloud users commonly use their extension/telephone
        # number as the emergency caller ID.  Use it when no separate E911
        # field is supplied by the API.
        if not emergency_caller_id:
            emergency_caller_id = str(_deep_value(
                raw, "caller_id_number", "caller-id-number", "callerid_number",
                "callerid-number", "cid_number", "cid-number",
                default=resolved_extension or resolved_username,
            )).strip()

        profile = {
            "username": resolved_username,
            "extension": resolved_extension,
            "first_name": first_name,
            "last_name": last_name,
            "display_name": display_name or " ".join(part for part in (first_name, last_name) if part).strip(),
            "email": str(_deep_value(raw, "email", "email_address", "email-address", "emailaddress", default=list_match.get("email", ""))).strip(),
            "department": str(_deep_value(raw, "department", "department_name", "department-name", default=list_match.get("department", ""))).strip(),
            "caller_id_name": caller_id_name,
            "caller_id_number": str(_deep_value(raw, "caller_id_number", "caller-id-number", "callerid_number", "callerid-number", "cid_number", "cid-number")).strip(),
            "emergency_caller_id": emergency_caller_id,
            "emergency_caller_id_configured": emergency_caller_id_configured,
            "time_zone": str(_deep_value(raw, "time_zone", "time-zone", "timezone", "tz", default="US/Eastern")).strip(),
            "language": str(_deep_value(raw, "language-token", "language_token", "language", "language_code", "language-code", "lang", default="en_US")).strip() or "en_US",
            "area_code": str(_deep_value(raw, "area_code", "area-code", "areacode")).strip(),
            "ring_seconds": str(_deep_value(raw, "ring-no-answer-timeout-seconds", default="60")).strip() or "60",
            "scope": str(_deep_value(raw, "scope", "user_scope", "user-scope", "scope_name", "scope-name", "user_type", "user-type", "type")).strip(),
            "enabled": _enabled(raw),
            "voicemail_enabled": _yes(_deep_value(raw, "voicemail-enabled", "vmail_enabled", default="yes"), True),
            "voicemail_limit_mb": 50,
            "raw": raw,
        }
        profile["voicemail_notifications"] = _voicemail_notification_state(raw, profile["email"])
        profile["voicemail_notification_enabled"] = profile["voicemail_notifications"]["enabled"]
        profile["voicemail_notification_email"] = profile["voicemail_notifications"]["recipient"]
        profile["voicemail_email_type"] = profile["voicemail_notifications"]["email_type"]
        profile["voicemail_after_notification"] = profile["voicemail_notifications"]["after_action"]
        profile["hidden_reason"] = self.hidden_reason(profile, domain.strip().lower().rstrip("."))
        profile["hidden"] = profile["hidden_reason"] is not None
        return profile


    def create(self, domain: str, payload: dict[str, Any]) -> Any:
        """Create one live DigiCloud user in an approved domain."""
        extension = re.sub(r"\D", "", str(payload.get("extension") or ""))
        first_name = str(payload.get("first_name") or "").strip()
        last_name = str(payload.get("last_name") or "").strip()
        email = str(payload.get("email") or "").strip()
        if not (3 <= len(extension) <= 16):
            raise ValueError("Extension must contain between 3 and 16 digits.")
        if not first_name or not last_name:
            raise ValueError("First name and last name are required.")
        if not email or "@" not in email:
            raise ValueError("A valid email address is required.")

        caller_number = re.sub(r"\D", "", str(payload.get("caller_id_number") or extension))
        emergency_number = re.sub(r"\D", "", str(payload.get("emergency_caller_id") or caller_number or extension))
        caller_name = str(payload.get("caller_id_name") or f"{first_name} {last_name}").strip()
        body: dict[str, Any] = {
            "synchronous": "yes",
            "user": extension,
            "name-first-name": first_name,
            "name-last-name": last_name,
            "login-username": str(payload.get("login_username") or f"{extension}@{domain}").strip(),
            "email-address": email,
            "user-scope": "Basic User",
            "department": str(payload.get("department") or "").strip(),
            "time-zone": str(payload.get("time_zone") or "US/Eastern").strip(),
            "language-token": str(payload.get("language") or "en_US").strip(),
            "area-code": int(str(payload.get("area_code") or "803").strip()),
            "dial-plan": str(payload.get("dial_plan") or domain).strip(),
            "dial-policy": str(payload.get("dial_policy") or "US and Canada").strip(),
            "caller-id-name": caller_name,
            "caller-id-number": caller_number,
            "caller-id-number-emergency": emergency_number,
            "voicemail-enabled": "yes" if payload.get("voicemail_enabled", True) else "no",
            "voicemail-user-control-enabled": "yes" if payload.get("voicemail_enabled", True) else "no",
            # DigiCloud reports voicemail storage in KB. Residential users use
            # a fixed 50 MB allocation.
            "data_limit": 50000,
            "vmail_enabled": "yes" if payload.get("voicemail_enabled", True) else "no",
            "vmail_notify": str(payload.get("voicemail_notification_email") or email).strip() if payload.get("voicemail_notification_enabled") else "",
            "vmail_notify_enabled": _voicemail_notification_token(
                bool(payload.get("voicemail_notification_enabled")),
                str(payload.get("voicemail_email_type") or "attachment"),
                str(payload.get("voicemail_after_notification") or "trash"),
            ),
            "call-screening-enabled": "yes",
            # NetSapiens v2 uses the legacy user fields returned by the live API
            # for directory behavior. New users should remain private unless an
            # administrator intentionally enables these options later.
            "dir_anc": "no",
            "dir_list": "no",
        }
        voicemail_pin = re.sub(r"\D", "", str(payload.get("voicemail_pin") or ""))
        if voicemail_pin:
            body["voicemail-login-pin"] = voicemail_pin
        created = self.client.request(
            "POST",
            f"/domains/{quote(domain, safe='')}/users",
            json=body,
        )

        # Domain templates can reapply directory defaults during provisioning.
        # Enforce both values again on the completed user using the exact fields
        # exposed by the NetSapiens v2 user schema.
        self.client.request(
            "PUT",
            f"/domains/{quote(domain, safe='')}/users/{quote(extension, safe='')}",
            params={"synchronous": "yes"},
            json={
                "dir_anc": "no",
                "dir_list": "no",
                "data_limit": 50000,
                "vmail_enabled": "yes" if payload.get("voicemail_enabled", True) else "no",
                "vmail_notify": str(payload.get("voicemail_notification_email") or email).strip() if payload.get("voicemail_notification_enabled") else "",
                "vmail_notify_enabled": _voicemail_notification_token(
                    bool(payload.get("voicemail_notification_enabled")),
                    str(payload.get("voicemail_email_type") or "attachment"),
                    str(payload.get("voicemail_after_notification") or "trash"),
                ),
            },
        )
        return created

    def delete(self, domain: str, username: str) -> Any:
        """Permanently delete one live DigiCloud user."""
        return self.client.request(
            "DELETE",
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}",
            params={"synchronous": "yes"},
        )

    def update_ring_timeout(self, domain: str, username: str, seconds: int) -> Any:
        """Update the user-level unanswered ring timeout used by all answering rules."""
        if seconds < 5 or seconds > 120 or seconds % 5 != 0:
            raise ValueError("Ring duration must be between 5 and 120 seconds in 5-second increments")
        return self.client.request(
            "PUT",
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}",
            params={"synchronous": "yes"},
            json={"ring-no-answer-timeout-seconds": int(seconds)},
        )

    def update_voicemail_settings(self, domain: str, username: str, payload: dict[str, Any]) -> Any:
        """Update voicemail notification settings using the NetSapiens v2 user fields.

        The user PUT requires the profile identity fields even when only a
        voicemail setting changes. Sending a partial legacy payload can return
        success while silently discarding the notification values.
        """
        current = self.get(domain, username)
        enabled = bool(payload.get("voicemail_notification_enabled"))
        recipient = str(payload.get("voicemail_notification_email") or "").strip()
        behavior = _voicemail_notification_token(
            enabled,
            str(payload.get("voicemail_email_type") or "attachment"),
            str(payload.get("voicemail_after_notification") or "trash"),
        )
        # The v2 PUT schema requires ``email`` and expects
        # the login identity alongside the profile identity fields.  DigiCloud
        # can return HTTP success while ignoring the voicemail notification
        # fields when those required names are missing or incorrect.
        body = {
            "domain": domain,
            "user": str(username),
            "name-first-name": current.get("first_name") or "User",
            "name-last-name": current.get("last_name") or str(username),
            "login-username": str(
                _deep_value(current.get("raw") or {}, "login-username", "subscriber_login", default=f"{username}@{domain}")
                or f"{username}@{domain}"
            ).strip(),
            "email": current.get("email") or recipient,
            "user-scope": current.get("scope") or "Basic User",
            "voicemail-enabled": "yes" if payload.get("voicemail_enabled", True) else "no",
            "limits-max-data-storage-kilobytes": 50000,
            "email-send-alert-new-voicemail-cc-list-csv": recipient if enabled else "",
            "email-send-alert-new-voicemail-behavior": behavior if enabled else "no",
            "email-send-alert-new-voicemail-enabled": "yes" if enabled else "no",
        }
        return self.client.request(
            "PUT",
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}",
            params={"synchronous": "yes"},
            json=body,
        )

    def update(self, domain: str, username: str, payload: dict[str, Any]) -> Any:
        """Update one DigiCloud user using the provider's hyphenated API fields.

        NOP keeps friendly snake_case form names internally.  NetSapiens/DigiCloud
        v2 expects the field names returned by the live API, such as
        ``caller-id-name`` and ``language-token``.
        """
        first_name = str(payload.get("first_name") or "").strip()
        last_name = str(payload.get("last_name") or "").strip()
        supplied_caller_name = str(payload.get("caller_id_name") or "").strip()
        profile_name = " ".join(part for part in (first_name, last_name) if part).strip()
        # DigiCloud exposes caller-id-name as the user's display/customer name
        # on this platform, so edits to First/Last Name must update that field.
        resolved_caller_name = profile_name or supplied_caller_name

        body: dict[str, Any] = {
            "email": str(payload.get("email") or "").strip(),
            "department": str(payload.get("department") or "").strip(),
            "caller-id-name": resolved_caller_name,
            "caller-id-number": str(payload.get("caller_id_number") or "").strip(),
            "caller-id-number-emergency": str(payload.get("emergency_caller_id") or "").strip(),
            "time-zone": str(payload.get("time_zone") or "").strip(),
            "language-token": str(payload.get("language") or "").strip(),
            "area-code": str(payload.get("area_code") or "").strip(),
        }

        enabled = payload.get("enabled")
        if enabled is not None:
            body["account-status"] = "active" if bool(enabled) else "disabled"

        return self.client.request(
            "PUT",
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}",
            params={"synchronous": "yes"},
            json=body,
        )
