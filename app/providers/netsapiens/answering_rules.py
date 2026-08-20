from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from app.providers.netsapiens.client import NetSapiensClient


TOKEN_LABELS = {
    '<owndevices>': ('All User Devices', 'devices'),
    '<voicemail>': ('Voicemail', 'voicemail'),
    '<reject>': ('Reject Call', 'reject'),
    '<busy>': ('Busy Signal', 'busy'),
    '<forward>': ('Forward', 'forward'),
    '<hangup>': ('End Call', 'reject'),
}

STRATEGY_LABELS = {
    'simultaneousring': 'Simultaneous Ring',
    'simring': 'Simultaneous Ring',
    'sequentialring': 'Sequential Ring',
    'callforward': 'Call Forward',
    'forwarddestination': 'Call Forward',
    'ringusers': 'Ring Users',
    'ringdestination': 'Ring Destination',
    'destination': 'Routing Destination',
}


def _key(value: str) -> str:
    return str(value).lower().replace('_', '').replace('-', '').replace(' ', '')


def _value(row: dict[str, Any], *names: str, default: Any = '') -> Any:
    wanted = {_key(name) for name in names}
    for key, value in row.items():
        if _key(key) in wanted and value not in (None, ''):
            return value
    return default


def _rows(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]
    if isinstance(result, dict):
        for key in ('data', 'items', 'records', 'answer-rules', 'answerrules', 'rules'):
            value = result.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [result] if result else []
    return []


def _yes(value: Any) -> bool | None:
    if value in (None, ''):
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {'yes', 'true', '1', 'enabled', 'active', 'on'}:
        return True
    if normalized in {'no', 'false', '0', 'disabled', 'inactive', 'off'}:
        return False
    return None


def _format_phone(value: str) -> str:
    digits = re.sub(r'\D', '', value)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
    return value


def _destination(value: Any) -> dict[str, str]:
    raw = str(value).strip()
    token = TOKEN_LABELS.get(raw.lower())
    if token:
        return {'raw': raw, 'label': token[0], 'type': token[1]}
    if '@' in raw:
        return {'raw': raw, 'label': raw, 'type': 'sip'}
    digits = re.sub(r'\D', '', raw)
    if len(digits) in {10, 11}:
        return {'raw': raw, 'label': _format_phone(raw), 'type': 'phone'}
    if raw.isdigit() and 2 <= len(raw) <= 7:
        return {'raw': raw, 'label': f'Extension {raw}', 'type': 'extension'}
    return {'raw': raw, 'label': raw, 'type': 'unknown'}


def _parameter_values(value: Any) -> list[Any]:
    """Return destinations from the different answer-rule shapes used by NS-API."""
    if value in (None, '', [], {}):
        return []
    if isinstance(value, list):
        values: list[Any] = []
        for item in value:
            values.extend(_parameter_values(item))
        return values
    if isinstance(value, dict):
        nested = _value(
            value,
            'parameters', 'destinations', 'destination', 'value', 'user', 'number',
            'parameter', 'target', default='',
        )
        if nested not in (None, '', [], {}):
            return _parameter_values(nested)
        return []
    return [value]


def _extract_routing(raw: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    """Derive the friendly routing summary from a full NS-API answer rule.

    Forwarding is evaluated before simultaneous ring.  A rule can retain its
    normal simultaneous-ring fallback while also having an enabled forwarding
    condition, so treating simultaneous ring as the only strategy hides a
    successfully saved forward in NOP.
    """
    forward_aliases = (
        ('Always', ('forward-always', 'call-forward-always')),
        ('On Active', ('forward-on-active', 'call-forward-on-active', 'call-forward-active')),
        ('When Busy', ('forward-on-busy', 'call-forward-busy', 'forward-busy', 'call-forward-when-busy')),
        ('When Unanswered', ('forward-no-answer', 'call-forward-no-answer', 'call-forward-unanswered')),
        ('When Offline', ('forward-when-unregistered', 'call-forward-offline', 'forward-offline', 'call-forward-when-offline')),
    )

    forward_values: list[Any] = []
    active_forward_labels: list[str] = []
    for label, aliases in forward_aliases:
        value = _value(raw, *aliases, default=None)
        if value in (None, '', [], {}):
            continue

        enabled = None
        if isinstance(value, dict):
            enabled = _yes(_value(value, 'enabled', 'active', default=None))
            values = _parameter_values(value)
        else:
            # Some NS-API versions expose the forward destination directly.
            enabled = _yes(value)
            values = [] if enabled is not None else _parameter_values(value)

        if enabled is True or (enabled is None and values):
            active_forward_labels.append(label)
            forward_values.extend(values)

    if active_forward_labels:
        destinations: list[dict[str, str]] = []
        seen: set[str] = set()
        for value in forward_values:
            item = _destination(value)
            if item['raw'] and item['raw'] not in seen:
                destinations.append(item)
                seen.add(item['raw'])
        suffix = active_forward_labels[0] if len(active_forward_labels) == 1 else 'Multiple Conditions'
        return f'Call Forward — {suffix}', destinations

    strategy = 'Provider Routing'
    values: list[Any] = []
    for key, value in raw.items():
        normalized_key = _key(key)
        if normalized_key not in STRATEGY_LABELS:
            continue

        # Do not report a disabled routing block as the active strategy.
        if isinstance(value, dict) and _yes(_value(value, 'enabled', default=None)) is False:
            continue

        strategy = STRATEGY_LABELS[normalized_key]
        values.extend(_parameter_values(value))

    if not values:
        direct = _value(raw, 'answer-rule-destination', 'forward-destination', 'destination', default='')
        values.extend(_parameter_values(direct))

    destinations: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        item = _destination(value)
        if item['raw'] and item['raw'] not in seen:
            destinations.append(item)
            seen.add(item['raw'])
    return strategy, destinations


class NetSapiensAnsweringRules:
    """Live answering-rule read and update operations for DigiCloud users."""

    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    @staticmethod
    def _normalize(raw: dict[str, Any], index: int = 1) -> dict[str, Any]:
        timeframe = str(_value(raw, 'time-frame', 'timeframe', 'time-frame-name', 'timeframe-name', default='*')).strip() or '*'
        priority_raw = _value(raw, 'ordinal-priority', 'priority', 'index', 'order', 'rule-order', default=index)
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError):
            priority = index

        strategy, destinations = _extract_routing(raw)
        enabled = _yes(_value(raw, 'enabled', 'answer-rule-enabled', default=None))
        is_active = _yes(_value(raw, 'is-active', 'active-now', default=None))
        is_default = timeframe.strip().lower() in {'*', 'default', 'always'}
        return {
            'priority': priority,
            'timeframe': timeframe,
            'timeframe_label': 'Default' if is_default else timeframe,
            'is_default': is_default,
            'enabled': enabled,
            'is_active': is_active,
            'strategy': strategy,
            'destinations': destinations,
            'raw': raw,
        }

    def _read_specific(self, domain: str, username: str, timeframe: str) -> tuple[dict[str, Any], Any]:
        result = self.client.request(
            'GET',
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}/answerrules/{quote(timeframe, safe='')}",
        )
        rows = _rows(result)
        if not rows:
            raise ValueError(f"Answering rule timeframe not found: {timeframe}")
        matching = next(
            (row for row in rows if str(_value(row, 'time-frame', 'timeframe', default=timeframe)) == str(timeframe)),
            rows[0],
        )
        return matching, result

    def list(self, domain: str, username: str) -> tuple[list[dict[str, Any]], Any]:
        collection = self.client.request(
            'GET',
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}/answerrules",
            params={'limit': 1000},
        )
        normalized: list[dict[str, Any]] = []
        details: dict[str, Any] = {}
        for index, summary in enumerate(_rows(collection), start=1):
            timeframe = str(_value(summary, 'time-frame', 'timeframe', 'time-frame-name', 'timeframe-name', default='*')).strip() or '*'
            raw = summary
            try:
                detail, detail_response = self._read_specific(domain, username, timeframe)
                # Preserve list-only fields such as priority/active status while
                # using the full timeframe record for routing details.
                raw = {**summary, **detail}
                details[timeframe] = detail_response
            except Exception as exc:
                # Older providers may not expose the detail endpoint.  The
                # collection response remains a safe fallback for display.
                details[timeframe] = {'detail_error': str(exc)}
            normalized.append(self._normalize(raw, index))
        normalized.sort(key=lambda row: (row['priority'], 0 if row['is_default'] else 1, row['timeframe'].lower()))
        return normalized, {'collection': collection, 'details': details}

    def get(self, domain: str, username: str, timeframe: str) -> dict[str, Any]:
        raw, _ = self._read_specific(domain, username, timeframe)
        return self._normalize(raw)

    @staticmethod
    def editor_state(current_raw: dict[str, Any]) -> dict[str, Any]:
        """Translate a provider rule into the DigiCloud-style editor fields."""
        def block(*names: str) -> dict[str, Any]:
            value = _value(current_raw, *names, default={})
            return value if isinstance(value, dict) else {}

        def destination_from(value: dict[str, Any]) -> str:
            params = _value(value, "parameters", "destinations", "destination", default=[])
            if isinstance(params, list) and params:
                first = params[0]
                if isinstance(first, dict):
                    return str(_value(first, "destination", "value", "number", "user", default=""))
                return str(first)
            if params not in (None, "", [], {}):
                return str(params)
            return ""

        forwards = {}
        aliases = {
            "always": ("forward-always", "call-forward-always"),
            "on_active": ("forward-on-active", "call-forward-on-active", "call-forward-active"),
            "busy": ("forward-on-busy", "call-forward-busy", "forward-busy", "call-forward-when-busy"),
            "unanswered": ("forward-no-answer", "call-forward-no-answer", "call-forward-unanswered"),
            "offline": ("forward-when-unregistered", "call-forward-offline", "forward-offline", "call-forward-when-offline"),
        }
        for name, keys in aliases.items():
            item = block(*keys)
            forwards[name] = {
                "enabled": _yes(_value(item, "enabled", default="no")) is True,
                "destination": destination_from(item),
            }

        simultaneous = block("simultaneous-ring", "simultaneousring")
        params = _value(simultaneous, "parameters", "destinations", default=[])
        if not isinstance(params, list):
            params = [params] if params not in (None, "") else []
        raw_destinations = []
        for item in params:
            if isinstance(item, dict):
                item = _value(item, "destination", "value", "number", "user", default="")
            value = str(item).strip()
            if value:
                raw_destinations.append(value)
        own_devices = any(v.lower() == "<owndevices>" for v in raw_destinations)
        additional = [v for v in raw_destinations if v.lower() != "<owndevices>"]

        dnd = block("do-not-disturb", "donotdisturb", "dnd")
        screening = block("call-screening", "callscreening")
        just_ring = _yes(_value(current_raw, "just-ring-users-extension", "just-ring-user-extension", default="no")) is True

        # DigiCloud treats Forward Always and Simultaneous Ring as mutually
        # exclusive routing modes. Some API responses retain the previous
        # simultaneous-ring block after Forward Always is enabled, so prefer
        # Forward Always when normalizing the editor state.
        simultaneous_enabled = _yes(_value(simultaneous, "enabled", default="no")) is True
        if forwards["always"]["enabled"]:
            simultaneous_enabled = False

        return {
            "enabled": _yes(_value(current_raw, "enabled", "answer-rule-enabled", default="yes")) is not False,
            "do_not_disturb": _yes(_value(dnd, "enabled", default=_value(current_raw, "do-not-disturb", default="no"))) is True,
            "call_screening": _yes(_value(screening, "enabled", default=_value(current_raw, "call-screening", default="no"))) is True,
            "forwards": forwards,
            "simultaneous_enabled": simultaneous_enabled,
            "include_extension": _yes(_value(simultaneous, "include-users-extension", "include-user-extension", default="no")) is True,
            "ring_all_phones": _yes(_value(simultaneous, "ring-all-users-phones", "ring-all-phones", default="yes" if own_devices else "no")) is True,
            "answer_confirmation": _yes(_value(simultaneous, "answer-confirmation", "answer-confirmation-for-offnet", default="no")) is True,
            "simultaneous_destinations": additional,
            "just_ring_extension": just_ring,
        }

    @staticmethod
    def build_update_payload(
        current_raw: dict[str, Any], *, enabled: bool, do_not_disturb: bool,
        call_screening: bool, forwards: dict[str, dict[str, Any]],
        simultaneous_enabled: bool, include_extension: bool,
        ring_all_phones: bool, answer_confirmation: bool,
        simultaneous_destinations: list[str], just_ring_extension: bool,
    ) -> dict[str, Any]:
        """Preserve unknown provider fields and replace DigiCloud ring-strategy fields."""
        payload = dict(current_raw)
        payload["enabled"] = "yes" if enabled else "no"
        payload["do-not-disturb"] = {"enabled": "yes" if do_not_disturb else "no"}
        payload["call-screening"] = {"enabled": "yes" if call_screening else "no"}
        forward_keys = {
            "always": "forward-always",
            "on_active": "forward-on-active",
            "busy": "forward-on-busy",
            "unanswered": "forward-no-answer",
            "offline": "forward-when-unregistered",
        }
        # Remove aliases managed by this editor before writing canonical keys.
        managed = {
            "callforwardalways", "forwardalways", "callforwardonactive", "forwardonactive",
            "callforwardactive", "callforwardbusy", "forwardonbusy", "forwardbusy", "callforwardwhenbusy",
            "callforwardnoanswer", "forwardnoanswer", "callforwardunanswered",
            "callforwardoffline", "forwardwhenunregistered", "forwardoffline", "callforwardwhenoffline",
        }
        for key in list(payload):
            if _key(key) in managed:
                payload.pop(key, None)

        for name, provider_key in forward_keys.items():
            item = forwards.get(name, {})
            destination = str(item.get("destination", "")).strip()
            payload[provider_key] = {
                "enabled": "yes" if bool(item.get("enabled")) else "no",
                "parameters": [destination] if destination else [],
            }

        clean: list[str] = []
        seen: set[str] = set()
        if ring_all_phones:
            clean.append("<OwnDevices>")
            seen.add("<OwnDevices>")
        for value in simultaneous_destinations:
            value = str(value).strip()
            if value and value not in seen:
                clean.append(value)
                seen.add(value)

        payload["simultaneous-ring"] = {
            "enabled": "yes" if simultaneous_enabled and not just_ring_extension else "no",
            "include-users-extension": "yes" if include_extension else "no",
            "ring-all-users-phones": "yes" if ring_all_phones else "no",
            "answer-confirmation": "yes" if answer_confirmation else "no",
            "parameters": clean,
        }
        payload["just-ring-users-extension"] = "yes" if just_ring_extension else "no"
        return payload

    def update(
        self, domain: str, username: str, timeframe: str, *, enabled: bool,
        do_not_disturb: bool, call_screening: bool,
        forwards: dict[str, dict[str, Any]], simultaneous_enabled: bool,
        include_extension: bool, ring_all_phones: bool,
        answer_confirmation: bool, simultaneous_destinations: list[str],
        just_ring_extension: bool,
    ) -> tuple[dict[str, Any], Any]:
        current = self.get(domain, username, timeframe)
        payload = self.build_update_payload(
            current["raw"], enabled=enabled, do_not_disturb=do_not_disturb,
            call_screening=call_screening, forwards=forwards,
            simultaneous_enabled=simultaneous_enabled,
            include_extension=include_extension, ring_all_phones=ring_all_phones,
            answer_confirmation=answer_confirmation,
            simultaneous_destinations=simultaneous_destinations,
            just_ring_extension=just_ring_extension,
        )
        # Answer-rule edits are updates to one existing timeframe.  POSTing to
        # the collection creates a rule and may be accepted as a no-op for an
        # existing timeframe.  The NetSapiens v2 update endpoint is PUT on the
        # timeframe-specific resource.
        result = self.client.request(
            "PUT",
            f"/domains/{quote(domain, safe='')}/users/{quote(username, safe='')}/answerrules/{quote(timeframe, safe='')}",
            params={"synchronous": "yes"},
            json=payload,
        )
        return payload, result
