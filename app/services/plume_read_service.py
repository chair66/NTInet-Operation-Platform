from __future__ import annotations

from dataclasses import dataclass
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Any
from urllib.parse import quote

from app.providers.plume.client import PlumeClient, plume_client


def _items(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "results", "nodes", "devices", "locations"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
    return [payload] if payload else []


def _object(payload: Any) -> dict:
    """Unwrap one API object without mistaking its child devices for itself."""
    if not isinstance(payload, dict):
        return {}
    for key in ("data", "item", "result", "node"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload


def _value(row: dict, *paths: str, default: Any = "") -> Any:
    for path in paths:
        current: Any = row
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current not in (None, "", [], {}):
            return current
    return default


def _integer(value: Any) -> int | None:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> float | None:
    if isinstance(value, dict):
        for key in ("value", "mbps", "speed", "result", "rate"):
            if key in value:
                parsed = _number(value[key])
                if parsed is not None:
                    return parsed
        for child in value.values():
            parsed = _number(child)
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if not match:
            return None
        value = match.group(0)
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _count(value: Any) -> int | None:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        nested = _value(value, "count", "total", "connected", default=None)
        return _integer(nested)
    return _integer(value)


def _scalar_text(value: Any) -> str:
    return str(value).strip() if isinstance(value, (str, int, float)) else ""


def _display_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(filter(None, (_scalar_text(item) for item in value)))
    return _scalar_text(value)


def _setting_text(value: Any) -> str:
    """Turn Plume's versioned steering/settings objects into support-friendly text."""
    if isinstance(value, bool):
        return "Enabled" if value else "Disabled"
    if isinstance(value, dict):
        enabled = value.get("enable", value.get("enabled"))
        automatic = value.get("auto", value.get("automatic"))
        if isinstance(enabled, bool):
            label = "Enabled" if enabled else "Disabled"
            if enabled and isinstance(automatic, bool):
                label += " · Auto" if automatic else " · Manual"
            return label
        return ", ".join(_recursive_values(value))
    return _display_text(value)


def _band_text(value: Any) -> str:
    raw = _scalar_text(value)
    labels = {
        "2g": "2.4 GHz", "2.4g": "2.4 GHz", "2.4ghz": "2.4 GHz",
        "5g": "5 GHz", "5gl": "5 GHz Lower", "5gu": "5 GHz Upper",
        "6g": "6 GHz", "60g": "60 GHz",
    }
    return labels.get(raw.lower(), raw)


def _security_text(value: Any) -> str:
    raw = _scalar_text(value)
    labels = {
        "psk2": "WPA2 PSK", "wpa2-psk": "WPA2 PSK", "wpa2_psk": "WPA2 PSK",
        "sae": "WPA3 SAE", "wpa3-sae": "WPA3 SAE", "open": "Open",
    }
    return labels.get(raw.lower(), raw.upper() if raw else "")


def _capabilities_text(value: Any) -> str:
    if not isinstance(value, dict):
        return _display_text(value)
    labels = []
    for key, label in (
        ("radio24", "2.4 GHz"), ("radio50", "5 GHz"),
        ("radio6", "6 GHz"), ("radio60", "60 GHz"),
    ):
        if value.get(key) is True:
            labels.append(label)
    return ", ".join(labels)


def _recursive_values(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            result.extend(_recursive_values(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_recursive_values(child))
    elif isinstance(value, (str, int, float)):
        text = str(value).strip()
        if text:
            result.append(text)
    return result


def _recursive_key(row: Any, wanted: set[str]) -> Any:
    if isinstance(row, dict):
        for key, value in row.items():
            if str(key).lower().replace("_", "") in wanted and value not in (None, "", [], {}):
                return value
        for value in row.values():
            found = _recursive_key(value, wanted)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(row, list):
        for value in row:
            found = _recursive_key(value, wanted)
            if found not in (None, "", [], {}):
                return found
    return None


def _recursive_numbers(row: Any, wanted_fragments: tuple[str, ...]) -> list[int]:
    values: list[int] = []
    if isinstance(row, dict):
        for key, value in row.items():
            normalized = str(key).lower().replace("_", "")
            if any(fragment in normalized for fragment in wanted_fragments):
                number = _integer(value)
                if number is not None:
                    values.append(number)
            values.extend(_recursive_numbers(value, wanted_fragments))
    elif isinstance(row, list):
        for value in row:
            values.extend(_recursive_numbers(value, wanted_fragments))
    return values


def _speed_records(payload: Any) -> list[dict]:
    """Find speed-test rows across the response envelopes used by Plume."""
    records: list[dict] = []
    if isinstance(payload, list):
        for value in payload:
            records.extend(_speed_records(value))
        return records
    if not isinstance(payload, dict):
        return records
    download_series = payload.get("downloadSpeeds")
    upload_series = payload.get("uploadSpeeds")
    if isinstance(download_series, list) or isinstance(upload_series, list):
        downloads = download_series if isinstance(download_series, list) else []
        uploads = upload_series if isinstance(upload_series, list) else []
        date_ranges = payload.get("statsDateRange")
        ranges = date_ranges if isinstance(date_ranges, list) else []
        for index in range(max(len(downloads), len(uploads), len(ranges))):
            down = downloads[index] if index < len(downloads) else None
            up = uploads[index] if index < len(uploads) else None
            date_row = ranges[index] if index < len(ranges) else None
            timestamp = ""
            for candidate in (down, up, date_row):
                if isinstance(candidate, dict):
                    timestamp = _display_text(_value(
                        candidate, "timestamp", "date", "completedAt", "end", "start",
                        default="",
                    ))
                    if timestamp:
                        break
            records.append({
                "download": _number(
                    _value(down, "value", "speed", "mbps", default=None)
                    if isinstance(down, dict) else down
                ),
                "upload": _number(
                    _value(up, "value", "speed", "mbps", default=None)
                    if isinstance(up, dict) else up
                ),
                "testedAt": timestamp,
                "status": "complete",
            })
        failed = payload.get("failedSpeedTests")
        if isinstance(failed, list):
            for item in failed:
                if isinstance(item, dict):
                    records.append({**item, "status": item.get("status") or "failed"})
        return records
    speed_keys = {
        "download", "downloadspeed", "downloadmbps", "upload", "uploadspeed",
        "uploadmbps", "downloadrate", "uploadrate", "requestid", "speedtestid",
        "downlink", "uplink", "downlinkmbps", "uplinkmbps", "rx", "tx",
    }
    normalized_keys = {str(key).lower().replace("_", "") for key in payload}
    if normalized_keys & speed_keys or any(
        ("download" in key or "upload" in key) and ("speed" in key or "rate" in key or "mbps" in key)
        for key in normalized_keys
    ):
        records.append(payload)
        return records
    for value in payload.values():
        records.extend(_speed_records(value))
    return records


def _latest_rssi(payload: Any) -> int | None:
    dated: list[tuple[str, int]] = []
    def visit(value: Any) -> None:
        if isinstance(value, dict):
            number = _integer(value.get("value"))
            stamp = _scalar_text(value.get("timestamp") or value.get("date") or value.get("time"))
            if number is not None and -120 <= number <= 0:
                dated.append((stamp, number))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(payload)
    if dated:
        dated.sort(key=lambda item: item[0], reverse=True)
        latest = dated[0][1]
        # Reports uses -95 as its no-current-sample floor. The Plume portal
        # suppresses that value rather than classifying it as poor signal.
        return latest if latest > -95 else None
    candidates = _recursive_numbers(payload, ("rssi", "signalstrength"))
    plausible = [value for value in candidates if -95 < value <= 0]
    return plausible[-1] if plausible else None


def _rssi_points(payload: Any) -> list[dict]:
    points: list[dict] = []
    if isinstance(payload, dict):
        number = _integer(payload.get("value"))
        timestamp = _display_text(
            payload.get("timestamp") or payload.get("date") or payload.get("time")
        )
        if number is not None and -95 < number <= 0:
            points.append({"timestamp": timestamp, "value": number})
        for value in payload.values():
            points.extend(_rssi_points(value))
    elif isinstance(payload, list):
        for value in payload:
            points.extend(_rssi_points(value))
    grouped: dict[str, list[int]] = {}
    for point in points:
        grouped.setdefault(point["timestamp"], []).append(point["value"])
    result = [
        {
            "timestamp": timestamp,
            "value": int(round(sum(set(values)) / len(set(values)))),
            "low": min(values),
            "high": max(values),
        }
        for timestamp, values in grouped.items() if values
    ]
    return sorted(result, key=lambda point: point["timestamp"], reverse=True)


def _records_containing(payload: Any, identifier: str) -> list[dict]:
    records: list[dict] = []
    if isinstance(payload, dict):
        values = {
            "".join(ch for ch in value if ch.isalnum()).lower()
            for value in _recursive_values(payload)
        }
        if identifier in values:
            records.append(payload)
        else:
            for value in payload.values():
                records.extend(_records_containing(value, identifier))
    elif isinstance(payload, list):
        for value in payload:
            records.extend(_records_containing(value, identifier))
    return records


def _status(row: dict) -> str:
    online = _value(row, "online", "isOnline", "connected", "isConnected", default=None)
    if isinstance(online, bool):
        return "online" if online else "offline"
    raw = str(_value(
        row, "connectionState", "connectivity", "status", "state", "health.status",
        default="unknown",
    )).strip().lower().replace(" ", "_")
    if raw in {"connected", "active", "up", "ready", "ok", "healthy"}:
        return "online"
    if raw in {"disconnected", "inactive", "down", "unreachable", "not_connected"}:
        return "offline"
    return raw or "unknown"


def _signal(row: dict) -> int | None:
    direct = _integer(_value(
        row, "signalStrength", "signal_strength", "rssi", "wlan.rssi", "mesh.rssi",
        "connection.rssi", default=None,
    ))
    if direct is not None:
        return direct
    candidates = _recursive_numbers(
        row, ("rssi", "signalstrength", "backhaulsignal", "backhaulrssi")
    )
    plausible = [value for value in candidates if -120 <= value <= 0]
    return max(plausible) if plausible else None


def _mac(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isalnum()).upper()
    return ":".join(raw[i:i + 2] for i in range(0, 12, 2)) if len(raw) == 12 else str(value or "")


@dataclass(slots=True)
class PlumeReadService:
    client: PlumeClient = plume_client

    def _resolve_customer_account(self, account_id: str) -> dict:
        """Resolve a CRM accountId to Plume's customer and location identifiers."""
        account_id = account_id.strip()
        if not account_id:
            return {}
        payload = self.client.get(
            f"Partners/customers/search/{quote(account_id, safe='')}",
            params={
                "field": "accountId",
                "exactMatch": "true",
                "startsWith": "false",
            },
        )
        matches = _items(payload)
        exact = next((
            row for row in matches
            if str(row.get("accountId") or "").strip().lower() == account_id.lower()
        ), None)
        return exact or (matches[0] if len(matches) == 1 else {})

    def resolve_customer_identity(self, search_string: str, search_entity: str) -> dict:
        """Resolve one native Plume customer/location through exact V2 search."""
        search_string = search_string.strip()
        search_entity = search_entity.strip()
        if not search_string or not search_entity:
            return {}
        payload = self.client.get(
            "Customers/v2/search",
            params={
                "searchString": search_string,
                "searchEntities": search_entity,
                "exactMatch": "true",
            },
        )
        matches = _items(payload)
        exact = [
            row for row in matches
            if str(row.get("matchedValue") or "").strip().lower()
            == search_string.lower()
        ]
        selected = exact[0] if len(exact) == 1 else (matches[0] if len(matches) == 1 else None)
        if not isinstance(selected, dict):
            return {}
        customer_id = str(selected.get("customerId") or "").strip()
        location_id = str(selected.get("locationIdToSelect") or "").strip()
        if not location_id:
            locations = selected.get("locations")
            if isinstance(locations, list) and len(locations) == 1 and isinstance(locations[0], dict):
                location_id = str(locations[0].get("locationId") or locations[0].get("id") or "").strip()
        if not customer_id or not location_id:
            return {}
        return {
            "customer_id": customer_id,
            "location_id": location_id,
            "customer_name": str(selected.get("customerName") or "").strip(),
            "customer_email": str(selected.get("customerEmail") or "").strip(),
        }

    def _lte_url(self, path: str) -> str:
        base = self.client.settings.plume_api_base_url.rstrip("/")
        if base.endswith("/api"):
            base = base[:-4]
        return f"{base}/lteservice/{path.lstrip('/')}"

    def _reports_url(self, path: str) -> str:
        base = self.client.settings.plume_api_base_url.rstrip("/")
        if base.endswith("/api"):
            base = base[:-4]
        return f"{base}/reports/{path.lstrip('/')}"

    def _reports_client_id(self) -> str:
        configured = getattr(self.client.settings, "plume_reports_client_id", "").strip()
        if configured:
            return configured
        header = self.client.settings.plume_authorization_header.strip()
        if header.lower().startswith("basic:"):
            header = header.split(":", 1)[1].strip()
        elif header.lower().startswith("basic "):
            header = header.split(" ", 1)[1].strip()
        try:
            decoded = base64.b64decode(header).decode("utf-8")
            return decoded.split(":", 1)[0].strip()
        except Exception:
            return ""

    def _reports_params(self, **params: Any) -> dict[str, Any]:
        client_id = self._reports_client_id()
        if client_id:
            params["client_id"] = client_id
        return params

    def run_speed_test(self, *, customer_id: str, location_id: str, node_id: str) -> dict:
        if not customer_id or not location_id or not node_id:
            raise ValueError("Plume customer, location, and pod IDs are required.")
        try:
            payload = self.client.put(
                self._lte_url(f"locations/{quote(location_id, safe='')}/speedTest"),
                json_body={"nodeId": node_id, "serverId": 0},
            )
        except Exception:
            # Non-LTE Plume locations use the Customer API action.
            payload = self.client.post(
                "Customers/"
                f"{quote(customer_id, safe='')}/locations/{quote(location_id, safe='')}"
                f"/nodes/{quote(node_id, safe='')}/speedTest"
            )
        return payload if isinstance(payload, dict) else {"data": payload}

    def network_credentials(self, *, customer_id: str, location_id: str) -> dict[str, str]:
        """Read the current primary Wi-Fi credentials without persisting them."""
        if not customer_id or not location_id:
            raise ValueError("Plume customer and location IDs are required.")
        prefix = (
            "Customers/"
            f"{quote(customer_id, safe='')}/locations/{quote(location_id, safe='')}"
        )
        # Plume exposes the SSID through a dedicated endpoint. Use it as the
        # authority because /wifiNetwork response envelopes vary by cloud.
        ssid_payload = self.client.get(prefix + "/wifiNetwork/ssid")
        ssid_source = _object(ssid_payload)
        ssid = _scalar_text(_value(
            ssid_source, "ssid", "name", "networkName", "network.ssid", default=""
        ))
        if not ssid and isinstance(ssid_payload, str):
            ssid = ssid_payload.strip()
        if not ssid:
            ssid = _scalar_text(_recursive_key(
                ssid_payload, {"ssid", "networkname"}
            ))
        # The full endpoint is still required for the PSK. Search the complete
        # payload so list/data/wifiNetwork envelopes are all supported.
        network_payload = self.client.get(prefix + "/wifiNetwork")
        network = _object(network_payload)
        password = _scalar_text(_value(
            network, "encryptionKey", "psk", "password", "passphrase",
            "network.encryptionKey", default=""
        ))
        if not password:
            password = _scalar_text(_recursive_key(
                network_payload, {"encryptionkey", "psk", "password", "passphrase"}
            ))
        if not ssid:
            raise ValueError("Plume did not return an SSID for this location.")
        if not password:
            raise ValueError(
                "Plume did not return the Wi-Fi password. The API token may not have access to it."
            )
        return {"ssid": ssid, "password": password}

    def snapshot(
        self,
        *,
        service_id: str = "",
        customer_id: str = "",
        location_id: str = "",
    ) -> dict:
        service_id = service_id.strip()
        customer_id = customer_id.strip()
        location_id = location_id.strip()
        location: dict = {}
        account_id = ""
        customer_profile: dict = {}

        # The association field may contain the CRM accountId (for example
        # chair_1003). Resolve it through the documented Partner search API.
        # If it is already a native Plume customer id, an empty/failed search is
        # harmless and the supplied id remains in use.
        if customer_id:
            supplied_customer_id = customer_id
            try:
                customer_match = self._resolve_customer_account(supplied_customer_id)
            except Exception:
                customer_match = {}
            if customer_match:
                account_id = str(customer_match.get("accountId") or supplied_customer_id).strip()
                customer_id = str(customer_match.get("id") or supplied_customer_id).strip()
                customer_locations = customer_match.get("locations")
                if not location_id and isinstance(customer_locations, list):
                    first_location = next((
                        row for row in customer_locations
                        if isinstance(row, dict) and row.get("id")
                    ), None)
                    if first_location:
                        location_id = str(first_location["id"]).strip()
        # Platypus stores the Plume pod serial as its service value. The documented
        # Partner node lookup returns the authoritative customerId and locationId,
        # so it takes precedence over cached/manual associations.
        if service_id:
            node_lookup_error: Exception | None = None
            try:
                payload = self.client.get(f"Partners/nodes/{quote(service_id, safe='')}")
            except Exception as exc:
                node_lookup_error = exc
                payload = {}
            matches = _items(payload)
            resolution_type = "pod serial"
            if not matches:
                location_lookup_error: Exception | None = None
                try:
                    location_payload = self.client.get(
                        f"Partners/locations/{quote(service_id, safe='')}"
                    )
                    matches = _items(location_payload)
                    resolution_type = "location/service"
                except Exception as location_exc:
                    location_lookup_error = location_exc
                    raise ValueError(
                        f"Plume could not resolve Platypus service value '{service_id}' "
                        f"as a pod serial or location/service. "
                        f"Pod lookup: {node_lookup_error or 'no match'}; "
                        f"location lookup: {location_lookup_error}"
                    ) from location_exc
            if not matches:
                raise ValueError(
                    f"Plume returned no location or pod for Platypus service value '{service_id}'."
                )
            # Partner node responses vary by cloud: some return the node
            # directly, while others wrap it in data/item/result/node.
            location = _object(matches[0]) or matches[0]
            resolved_location_id = str(_value(
                location, "locationId", "location.id", "location.locationId",
                "locationId.id", "location._id",
                *(('id', '_id') if resolution_type == 'location/service' else ()),
            )).strip()
            if not resolved_location_id:
                recursive_location_id = _recursive_key(
                    payload, {"locationid"}
                )
                if isinstance(recursive_location_id, dict):
                    recursive_location_id = _value(
                        recursive_location_id, "id", "_id", "locationId", default=""
                    )
                resolved_location_id = _scalar_text(recursive_location_id)
            resolved_customer_id = str(_value(
                location, "customerId", "userId", "ownerId", "customer.id",
                "customerId.id", "owner.id", "user.id", "location.customerId",
                "location.customer.id"
            )).strip()
            if not resolved_customer_id:
                recursive_customer_id = _recursive_key(
                    payload, {"customerid", "userid", "ownerid"}
                )
                if isinstance(recursive_customer_id, dict):
                    recursive_customer_id = _value(
                        recursive_customer_id, "id", "_id", "customerId", default=""
                    )
                resolved_customer_id = _scalar_text(recursive_customer_id)
            # For a successful node lookup these documented values are
            # authoritative, even when NOP has older manually stored IDs.
            location_id = resolved_location_id or location_id
            customer_id = resolved_customer_id or customer_id
            resolved_account_id = str(_value(
                location, "accountId", "customer.accountId", "location.accountId",
                default="",
            )).strip()
            if resolved_account_id and not account_id:
                try:
                    customer_match = self._resolve_customer_account(resolved_account_id)
                except Exception:
                    customer_match = {}
                if customer_match:
                    account_id = str(customer_match.get("accountId") or resolved_account_id)
                    customer_id = str(customer_match.get("id") or customer_id).strip()
                    if not location_id:
                        customer_locations = customer_match.get("locations")
                        if isinstance(customer_locations, list) and customer_locations:
                            location_id = str(customer_locations[0].get("id") or "").strip()
            if not location_id:
                raise ValueError(
                    f"Plume resolved '{service_id}' as a {resolution_type}, but its response did not include a location ID."
                )
        # Node lookup responses do not always expose the owning customer. Resolve
        # the now-known location through the partner endpoint to obtain it before
        # selecting the customer-scoped read APIs.
        if location_id and not customer_id:
            try:
                resolved_location_payload = self.client.get(
                    f"partners/locations/{quote(location_id, safe='')}"
                )
                resolved_locations = _items(resolved_location_payload)
                if resolved_locations:
                    resolved_location = resolved_locations[0]
                    if not location:
                        location = resolved_location
                    customer_id = str(_value(
                        resolved_location, "customerId", "userId", "ownerId",
                        "customer.id", "customerId.id", "owner.id", "user.id",
                        "location.customerId", "location.customer.id",
                    )).strip()
            except Exception:
                pass
        if not location_id:
            raise ValueError("A Plume service ID or location ID is required.")

        encoded_location = quote(location_id, safe="")
        nodes_path = f"gateway/locations/{encoded_location}/nodes"
        devices_path = f"gateway/locations/{encoded_location}/devices"
        node_params: dict[str, Any] | None = {
            "fields": "(*,interfaces,firmware,mesh,wlan,wan)"
        }
        device_params: dict[str, Any] | None = {
            "fields": "(*,wlan,mesh,kind(*,os(*),custom(*)))",
            "filter": '{"order":"lastSeenAt DESC"}',
        }
        if customer_id:
            encoded_customer = quote(customer_id, safe="")
            nodes_path = f"Customers/{encoded_customer}/locations/{encoded_location}/nodes"
            devices_path = f"Customers/{encoded_customer}/locations/{encoded_location}/devices"
            node_params = None
            device_params = {
                "daysOffline": max(int(self.client.settings.plume_device_days_offline), 0),
                "allSSIDs": "true",
            }
        try:
            nodes_payload = self.client.get(nodes_path, params=node_params)
        except Exception as exc:
            raise ValueError(
                f"Plume resolved location '{location_id}'"
                + (f" for customer '{customer_id}'" if customer_id else "")
                + f", but the pod lookup failed at /{nodes_path}: {exc}"
            ) from exc
        try:
            devices_payload = self.client.get(devices_path, params=device_params)
        except Exception as exc:
            raise ValueError(
                f"Plume resolved location '{location_id}'"
                + (f" for customer '{customer_id}'" if customer_id else "")
                + f", but the device lookup failed at /{devices_path}: {exc}"
            ) from exc
        raw_nodes = _items(nodes_payload)
        raw_devices = _items(devices_payload)
        alerts: dict = {}
        network_ssid = ""
        if customer_id:
            try:
                customer_profile = _object(self.client.get(
                    f"Customers/{quote(customer_id, safe='')}"
                ))
                account_id = _scalar_text(_value(
                    customer_profile, "accountId", "account.id", default=account_id
                )) or account_id
            except Exception:
                customer_profile = {}
            try:
                ssid_payload = self.client.get(
                    f"Customers/{quote(customer_id, safe='')}/locations/"
                    f"{encoded_location}/wifiNetwork/ssid"
                )
                network_ssid = _scalar_text(_value(
                    _object(ssid_payload), "ssid", "name", "network.ssid", default=""
                ))
            except Exception:
                try:
                    wlan_payload = self.client.get(
                        f"Customers/{quote(customer_id, safe='')}/locations/"
                        f"{encoded_location}/wlans"
                    )
                    wlan = next((row for row in _items(wlan_payload) if isinstance(row, dict)), {})
                    network_ssid = _scalar_text(_value(
                        wlan, "ssid", "name", "networkName", default=""
                    ))
                except Exception:
                    network_ssid = ""
            try:
                alerts = self.client.get(
                    f"Customers/{quote(customer_id, safe='')}/locations/{encoded_location}/alerts"
                )
            except Exception:
                # Nodes and devices remain useful when the token lacks the optional
                # customer-alert scope.
                alerts = {}

        # The list response is intentionally compact. The single-node response
        # includes richer nickname, backhaul, radio, and connected-client data.
        detailed_nodes: list[dict] = []
        for row in raw_nodes:
            base_pod = self._pod(row)
            try:
                detail_payload = self.client.get(
                    "Customers/"
                    f"{quote(customer_id, safe='')}/locations/{encoded_location}"
                    f"/nodes/{quote(base_pod['id'], safe='')}"
                ) if customer_id and base_pod["id"] else {}
                detail = _object(detail_payload)
                merged = {**row, **detail}
                # Detail responses may describe the gateway in shared fields.
                # Preserve the list row's unique physical-node identity.
                for identity_key in (
                    "id", "nodeId", "serialNumber", "serial", "mac", "macAddress",
                    "ethernetMac",
                ):
                    if row.get(identity_key) not in (None, "", [], {}):
                        merged[identity_key] = row[identity_key]
                resolved = self._pod(merged)
                if customer_id and resolved["name"] in {
                    resolved["id"], resolved["serial_number"], resolved["model"],
                    "Plume Pod",
                }:
                    try:
                        customer_detail = _object(self.client.get(
                            f"Customers/{quote(customer_id, safe='')}/nodes/"
                            f"{quote(base_pod['id'], safe='')}"
                        ))
                        merged = {**merged, **customer_detail}
                        for identity_key in (
                            "id", "nodeId", "serialNumber", "serial", "mac",
                            "macAddress", "ethernetMac",
                        ):
                            if row.get(identity_key) not in (None, "", [], {}):
                                merged[identity_key] = row[identity_key]
                    except Exception:
                        pass
                detailed_nodes.append(merged)
            except Exception:
                detailed_nodes.append(row)
        pods = self._deduplicate_pods([self._pod(row) for row in detailed_nodes])
        # Put the residential/master gateway first, followed by extender pods.
        pods.sort(key=lambda item: (item.get("role") != "gateway", item.get("name") or ""))
        lte_speed_items: list[dict] = []
        lte_speed_error = ""
        try:
            lte_speed_payload = self.client.get(
                self._lte_url(f"locations/{encoded_location}/speedTests"),
                params={"limit": 30, "granularity": "days"},
            )
            lte_speed_items = _speed_records(lte_speed_payload)
        except Exception as exc:
            lte_speed_error = f"LTE Service API: {exc}"
        if customer_id:
            for pod in pods:
                try:
                    history_notes: list[str] = []
                    normalized_pod_id = "".join(ch for ch in pod["id"] if ch.isalnum()).lower()
                    # Customer node records often embed the gateway's latest
                    # completed speed test. Use that authoritative result before
                    # querying the optional history/report endpoints.
                    embedded_speed = _value(pod.get("raw") or {}, "speedTest", default=None)
                    speed_items = _speed_records(embedded_speed)
                    if not speed_items:
                        speed_items = [
                            item for item in lte_speed_items
                            if normalized_pod_id and normalized_pod_id in {
                                "".join(ch for ch in value if ch.isalnum()).lower()
                                for value in _recursive_values(item)
                            }
                        ]
                    if not speed_items and len(pods) == 1:
                        speed_items = list(lte_speed_items)
                    if not speed_items and lte_speed_error:
                        history_notes.append(lte_speed_error)
                    speed_path = self._reports_url(
                        "Customers/"
                        f"{quote(customer_id, safe='')}/locations/{encoded_location}"
                        f"/nodes/{quote(pod['id'], safe='')}/results"
                    )
                    speed_params = self._reports_params(
                        granularity="days", limit=30, showFailedSpeedTests="true"
                    )
                    try:
                        if speed_items:
                            raise StopIteration
                        speed_payload = self.client.get(speed_path, params=speed_params)
                        speed_items = _speed_records(speed_payload)
                        if not speed_items:
                            keys = ", ".join(speed_payload.keys()) if isinstance(speed_payload, dict) else type(speed_payload).__name__
                            history_notes.append(f"Reports response fields: {keys or 'none'}")
                    except StopIteration:
                        pass
                    except Exception as exc:
                        speed_items = []
                        history_notes.append(f"Reports API: {exc}")
                    if not speed_items:
                        # Compatibility fallback for older Customer API releases.
                        try:
                            speed_payload = self.client.get(
                                "Customers/"
                                f"{quote(customer_id, safe='')}/locations/{encoded_location}"
                                f"/nodes/{quote(pod['id'], safe='')}/speedTestResults",
                                params=speed_params,
                            )
                            speed_items = _speed_records(speed_payload)
                            if not speed_items:
                                keys = ", ".join(speed_payload.keys()) if isinstance(speed_payload, dict) else type(speed_payload).__name__
                                history_notes.append(f"Customer response fields: {keys or 'none'}")
                        except Exception as exc:
                            history_notes.append(f"Customer API: {exc}")
                    tests = [self._speed_test(item) for item in speed_items]
                    tests = [item for item in tests if self._has_speed_result(item)]
                    if speed_items and not tests:
                        sample_keys = sorted({
                            str(key) for item in speed_items[:3] for key in item.keys()
                        })
                        history_notes.append(
                            "Unmapped speed-result fields: " + ", ".join(sample_keys)
                        )
                    tests.sort(key=lambda item: item["tested_at"], reverse=True)
                    pod["speed_tests"] = tests
                    pod["speed_test"] = tests[0] if tests else None
                    downloads = [item["download"] for item in tests if item["download"] is not None]
                    uploads = [item["upload"] for item in tests if item["upload"] is not None]
                    pod["speed_summary"] = {
                        "download_recent": downloads[0] if downloads else None,
                        "download_max": max(downloads) if downloads else None,
                        "download_min": min(downloads) if downloads else None,
                        "upload_recent": uploads[0] if uploads else None,
                        "upload_max": max(uploads) if uploads else None,
                        "upload_min": min(uploads) if uploads else None,
                    }
                    pod["speed_history_note"] = "; ".join(history_notes)
                except Exception:
                    # Speed-test history is optional and must not prevent the core
                    # pod and device health page from loading.
                    pod["speed_test"] = None
                    pod["speed_tests"] = []
                    pod["speed_summary"] = {}
                    pod["speed_history_note"] = "Unable to normalize the Plume speed-test response."
        pod_names: dict[str, str] = {}
        for pod in pods:
            for key in pod["aliases"]:
                if key:
                    normalized = "".join(ch for ch in str(key) if ch.isalnum()).lower()
                    if normalized:
                        pod_names[normalized] = pod["name"]
        devices = [self._device(row, pod_names) for row in raw_devices]
        try:
            signal_payload = self.client.get(
                self._lte_url(f"locations/{encoded_location}/signalStrength")
            )
            for device in devices:
                normalized_mac = "".join(
                    ch for ch in device["mac_address"] if ch.isalnum()
                ).lower()
                if not normalized_mac:
                    continue
                matching = _records_containing(signal_payload, normalized_mac)
                source = matching[0] if matching else signal_payload
                device["signal_strength"] = _latest_rssi(source)
        except Exception:
            pass
        # The LTE location response is not populated for every Plume deployment.
        # Fill table RSSI from the Reports API in parallel so one slow device does
        # not make the customer page unusable.
        def report_signal(device: dict) -> tuple[dict, int | None, str, bool]:
            mac = str(device.get("mac_address") or "").lower()
            if not mac:
                return device, None, "", False
            try:
                payload = self.client.get(
                    self._reports_url(
                        "Customers/"
                        f"{quote(customer_id, safe='')}/locations/{encoded_location}"
                        f"/devices/{quote(mac, safe='')}/rssi"
                    ),
                    params=self._reports_params(granularity="hours", limit=24),
                )
                current = _latest_rssi(payload)
                points = _rssi_points(payload)
                if current is not None:
                    timestamp = points[0]["timestamp"] if points else ""
                    return device, current, timestamp, True
                if points:
                    return device, points[0]["value"], points[0]["timestamp"], False
            except Exception:
                pass
            return device, device.get("signal_strength"), "", False

        if customer_id and devices:
            with ThreadPoolExecutor(max_workers=min(6, len(devices))) as executor:
                futures = [executor.submit(report_signal, device) for device in devices]
                for future in as_completed(futures):
                    try:
                        device, signal, timestamp, is_current = future.result()
                    except Exception:
                        continue
                    device["signal_strength"] = signal
                    device["signal_timestamp"] = timestamp
                    device["signal_is_current"] = is_current
        for pod in pods:
            associated_count = sum(
                1 for device in devices
                if device["status"] == "online" and device["pod_name"] == pod["name"]
            )
            pod["connected_device_count"] = max(pod["connected_device_count"], associated_count)
        return {
            "service_id": service_id,
            "account_id": account_id,
            "customer_id": customer_id,
            "location_id": location_id,
            "location_name": str(_value(location, "name", "location.name", default="")),
            "network_ssid": network_ssid,
            "customer_name": _scalar_text(_value(
                customer_profile, "name", "fullName", default=""
            )) or " ".join(filter(None, (
                _scalar_text(_value(customer_profile, "firstName", default="")),
                _scalar_text(_value(customer_profile, "lastName", default="")),
            ))),
            "customer_email": _scalar_text(_value(
                customer_profile, "email", "contact.email", default=""
            )),
            "resolution_type": resolution_type if service_id else "stored location",
            "pods": pods,
            "devices": devices,
            "connected_devices": [d for d in devices if d["status"] == "online"],
            "offline_devices": [d for d in devices if d["status"] != "online"],
            "alerts": alerts,
        }

    def device_detail(
        self, *, customer_id: str, location_id: str, mac_address: str,
        pod_names: dict[str, str] | None = None, network_id: str = "",
    ) -> dict:
        if not customer_id or not location_id or not mac_address:
            raise ValueError("Plume customer, location, and device MAC are required.")
        base_path = (
            "Customers/"
            f"{quote(customer_id, safe='')}/locations/{quote(location_id, safe='')}"
            "/devices/"
        )
        params = {"include": "bandwidthData,chartsData", "daysOffline": 30}
        compact_mac = "".join(ch for ch in mac_address if ch.isalnum())
        formatted_mac = ":".join(
            compact_mac[index:index + 2] for index in range(0, 12, 2)
        ) if len(compact_mac) == 12 else mac_address
        mac_values = list(dict.fromkeys((
            formatted_mac.lower(), formatted_mac, formatted_mac.upper(),
            compact_mac.lower(), compact_mac.upper(),
        )))
        payload: Any = {}
        first_exc: Exception | None = None
        for mac in mac_values:
            try:
                payload = self.client.get(
                    base_path + quote(mac, safe=""), params=params
                )
                break
            except Exception as exc:
                first_exc = first_exc or exc
        if not payload:
            raise first_exc or ValueError("Plume returned no device details.")
        row = _object(payload)
        device = self._device(row, pod_names or {})
        device.update(self.device_metadata(row))
        try:
            ssid_payload = self.client.get(
                "Customers/"
                f"{quote(customer_id, safe='')}/locations/{quote(location_id, safe='')}"
                "/wifiNetwork/ssid"
            )
            ssid = _scalar_text(_value(
                _object(ssid_payload), "ssid", "name", "network.ssid", default=""
            ))
            if ssid:
                device["ssid"] = ssid
        except Exception:
            pass
        return device

    def device_extras(
        self, *, customer_id: str, location_id: str, mac_address: str,
    ) -> dict:
        prefix = (
            "Customers/"
            f"{quote(customer_id, safe='')}/locations/{quote(location_id, safe='')}"
            "/devices/"
        )
        mac_values = [mac_address.lower(), mac_address]
        compact = "".join(ch for ch in mac_address if ch.isalnum()).upper()
        if compact and compact != mac_address:
            mac_values.append(compact)
        reports_device_path = (
            "Customers/"
            f"{quote(customer_id, safe='')}/locations/{quote(location_id, safe='')}"
            "/devices/{mac}"
        )

        type_row: dict = {}
        for mac in mac_values:
            try:
                type_row = _object(self.client.get(
                    self._reports_url(
                        reports_device_path.format(mac=quote(mac, safe=""))
                        + "/deviceTypeDetails"
                    ),
                    params=self._reports_params(),
                ))
                if type_row:
                    break
            except Exception:
                continue

        rssi_payload: Any = {}
        for mac in mac_values:
            try:
                rssi_payload = self.client.get(
                    self._reports_url(
                        reports_device_path.format(mac=quote(mac, safe="")) + "/rssi"
                    ),
                    params=self._reports_params(granularity="hours", limit=24),
                )
                break
            except Exception:
                continue
        points = _rssi_points(rssi_payload)
        values = [point["value"] for point in points]
        current = _latest_rssi(rssi_payload)
        if current is None:
            signal_health = "unknown"
        elif current >= -67:
            signal_health = "excellent"
        elif current >= -75:
            signal_health = "good"
        elif current >= -80:
            signal_health = "fair"
        else:
            signal_health = "poor"
        metadata = self.device_metadata(type_row)

        qoe_payload: Any = {}
        customer_location = (
            f"Customers/{quote(customer_id, safe='')}/locations/"
            f"{quote(location_id, safe='')}"
        )
        qoe_paths = [
            self._reports_url(reports_device_path + "/qoeMetricsV2"),
            self._reports_url(reports_device_path + "/qoeMetrics"),
            # Compatibility paths for other Plume API deployments.
            customer_location + "/flex/devices/{mac}/qoeMetricsV2",
            customer_location + "/flex/devices/{mac}/qoeMetrics",
            customer_location + "/devices/v2/{mac}/qoe",
            prefix + "{mac}/qoeMetricsV2",
            prefix + "{mac}/qoeMetrics",
        ]
        for path_template in qoe_paths:
            for mac in mac_values:
                try:
                    qoe_payload = self.client.get(
                        path_template.format(mac=quote(mac, safe="")),
                        params=self._reports_params(
                            granularity="hours", limit=24,
                            timestampISOFormat="true",
                        ) if path_template.startswith(("http://", "https://")) else {
                            "granularity": "hours", "limit": 24,
                            "timestampISOFormat": "true",
                        },
                    )
                    if qoe_payload:
                        break
                except Exception:
                    continue
            if qoe_payload:
                break

        stitch_payload: Any = {}
        for mac in mac_values:
            try:
                stitch_payload = self.client.get(
                    prefix + quote(mac, safe="") + "/stitchHistory"
                )
                break
            except Exception:
                continue
        stitch_rows = _items(stitch_payload)
        qoe_rows = qoe_payload.get("data", []) if isinstance(qoe_payload, dict) else []
        qoe_rows = [row for row in qoe_rows if isinstance(row, dict)]
        qoe_rows.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)
        latest_qoe = qoe_rows[0] if qoe_rows else qoe_payload
        metadata.update({
            "signal_strength": current,
            "signal_health": signal_health,
            "rssi_min": min(values) if values else None,
            "rssi_max": max(values) if values else None,
            "rssi_history": points[:48],
            "qoe_score": _number(_recursive_key(
                latest_qoe, {"weightedqoescore", "qoescore", "qoe", "score"}
            )),
            "latency": _number(_recursive_key(
                qoe_payload, {"latency", "latencyms", "rtt"}
            )),
            "jitter": _number(_recursive_key(
                qoe_payload, {"jitter", "jitterms"}
            )),
            "packet_loss": _number(_recursive_key(
                qoe_payload, {"packetloss", "packetlosspercent", "loss"}
            )),
            "predicted_wifi_speed": _number(_recursive_key(
                latest_qoe, {"averagepredictedwifispeed", "predictedwifispeed"}
            )),
            "minimum_wifi_speed": _number(_recursive_key(
                latest_qoe, {"minpredictedwifispeed"}
            )),
            "channel_utilization": _number(_recursive_key(
                latest_qoe, {"channelutilization"}
            )),
            "interference": _number(_recursive_key(
                latest_qoe, {"interference"}
            )),
            "stitch_history_count": len(stitch_rows),
            "stitch_last_seen": _display_text(_value(
                stitch_rows[0], "timestamp", "createdAt", "updatedAt", "date",
                default="",
            )) if stitch_rows else "",
        })
        return metadata

    @staticmethod
    def device_metadata(row: dict) -> dict:
        category = _scalar_text(_value(row, "category", "kind.category"))
        manufacturer = _scalar_text(_value(
            row, "brand", "manufacturer", "kind.brand", "kind.manufacturer"
        ))
        model = _scalar_text(_value(
            row, "model", "kind.model", "kind.type.model", "deviceModel", "name"
        ))
        classification_id = _scalar_text(_value(row, "kind.id", "type.id", "deviceType"))
        if not category:
            category = _scalar_text(_recursive_key(row, {"category"}))
        if not manufacturer:
            manufacturer = _scalar_text(_recursive_key(row, {"brand", "manufacturer"}))
        if not model:
            model = _scalar_text(_recursive_key(row, {"model", "devicemodel"}))
        if not classification_id:
            classification_id = _scalar_text(_recursive_key(
                row, {"devicetype", "classificationid"}
            ))
        return {
            "ssid": _scalar_text(_value(row, "ssid", "networkName", "wlan.ssid")),
            "channel": _scalar_text(_value(row, "channel", "wlan.channel")),
            "model": model,
            "manufacturer": manufacturer,
            "operating_system": _scalar_text(_value(
                row, "osName", "operatingSystem", "kind.os.name", "kind.osName"
            )),
            "operating_system_version": _scalar_text(_value(
                row, "osVersion", "kind.os.version", "kind.osVersion"
            )),
            "favorite": bool(_value(row, "favorite", "isFavorite", default=False)),
            "bandwidth_download": _number(_value(
                row, "bandwidth.downloadMb", "bandwidthData.downloadMb",
                "daily.downloadMb", "bandwidth.daily.download", default=None,
            )),
            "bandwidth_upload": _number(_value(
                row, "bandwidth.uploadMb", "bandwidthData.uploadMb",
                "daily.uploadMb", "bandwidth.daily.upload", default=None,
            )),
            "category": category,
            "classification_id": classification_id,
            "capabilities": _display_text(_value(
                row, "capabilities", "kind.capabilities", "wifiCapabilities",
                "wlan.capabilities", default="",
            )) or _capabilities_text(row.get("capabilities")),
            "wifi_standard": _display_text(_value(
                row, "wifiStandard", "phyMode", "wlan.standard", "wlan.phyMode",
                default="",
            )),
            "security": _security_text(_value(
                row, "security", "securityMode", "wlan.security", "wpaMode", default=""
            )),
            "first_connected": _scalar_text(_value(row, "firstConnectedAt", default="")),
            "connection_state_changed": _scalar_text(_value(
                row, "connectionStateChangeAt", default=""
            )),
            "interference": _number(_value(
                row, "interference", "interferencePercent", "wlan.interference",
                default=None,
            )),
            "alarms": _display_text(_value(row, "alarms", "alarm", default="")),
            "health": _scalar_text(_value(
                row, "healthStatus", "health.status", "health", default=""
            )),
            "opensync_steering": _setting_text(_value(
                row, "openSyncSteering", "opensyncSteering", "clientSteering",
                default=None,
            )),
            "cloud_steering": _setting_text(_value(
                row, "cloudSteering", "bandSteering", default=None
            )),
            "coverage_alarm": _scalar_text(_value(
                row, "coverageAlarm", "coverage.status", default=""
            )),
            "out_of_home_protection": _scalar_text(_value(
                row, "outOfHomeProtection", "securityPolicy.ohp", default=""
            )),
            "mac_stitching": _scalar_text(_value(
                row, "macStitching", "stitchingStatus", default=""
            )),
        }

    @staticmethod
    def _pod(row: dict) -> dict:
        pod_id = _scalar_text(_value(
            row, "serialNumber", "serial", "nodeId", "node.id", "id", default=""
        ))
        name = _scalar_text(_value(
            row, "roomName", "room.name", "room.label", "displayName", "podName",
            "customName", "nodeName", "label", "title", "nickname",
            "defaultName", "nodeInfo.nickname", "metadata.nickname", "config.nickname", "name",
            default=""
        ))
        if not name:
            name = _scalar_text(_recursive_key(
                row, {"nickname", "displayname", "podname", "customname", "nodename"}
            ))
        model = _scalar_text(_value(row, "model", "hardware.model", default=""))
        serial = _scalar_text(_value(
            row, "serialNumber", "serial", "nodeId", "node.id", default=""
        ))
        mac = _mac(_value(row, "mac", "macAddress", "ethernetMac", "interfaces.ethernet.mac"))
        if not name or name == model:
            name = serial or mac or pod_id or "Plume Pod"
        status = _status(row)
        health = str(_value(row, "healthStatus", "health.status", "health", default="")).lower()
        if not health:
            health = "healthy" if status == "online" else ("offline" if status == "offline" else "unknown")
        aliases = [pod_id, serial, mac]
        # Radio/interface identifiers are commonly used by the device response
        # when referring to its connected pod.
        for key, value in row.items():
            normalized_key = str(key).lower().replace("_", "")
            if "mac" in normalized_key or normalized_key in {"nodeid", "serialnumber"}:
                aliases.extend(_recursive_values(value))
        # Device records may refer to a pod radio/BSSID. Limit nested aliases to
        # node-owned interface data; connected-client MACs must never participate
        # in pod deduplication.
        for branch_name in ("interfaces", "radios", "radio", "wlan", "wan"):
            branch = row.get(branch_name)
            if branch is None:
                continue
            for value in _recursive_values(branch):
                compact = "".join(ch for ch in value if ch.isalnum())
                if len(compact) == 12:
                    aliases.append(value)
        reported_count = _count(_value(
            row, "connectedDeviceCount", "devicesCount", "clientCount",
            "connectedDevices", "clients", "devices", default=0,
        )) or 0
        is_gateway = bool(_value(
            row, "residentialGateway", "isMasterGateway", default=False
        ))
        return {
            "id": pod_id,
            "name": name,
            "model": model,
            "serial_number": serial,
            "mac_address": mac,
            "firmware": _scalar_text(_value(
                row, "firmwareVersion", "firmware.version", "firmware", default=""
            )),
            "role": "gateway" if is_gateway else (
                _scalar_text(_value(row, "role", "nodeRole", default="pod")) or "pod"
            ),
            "status": status,
            "health": health,
            "signal_strength": _signal(row),
            "signal_timestamp": "",
            "signal_is_current": False,
            "connected_device_count": reported_count,
            "aliases": list(dict.fromkeys(aliases)),
            "raw": row,
        }

    @staticmethod
    def _deduplicate_pods(pods: list[dict]) -> list[dict]:
        unique: list[dict] = []
        seen: dict[str, dict] = {}
        for pod in pods:
            identifiers = {
                "".join(ch for ch in str(value) if ch.isalnum()).lower()
                for value in pod["aliases"]
                if value
            }
            existing = next((seen[value] for value in identifiers if value in seen), None)
            if existing:
                existing["aliases"] = list(dict.fromkeys(existing["aliases"] + pod["aliases"]))
                existing["connected_device_count"] = max(
                    existing["connected_device_count"], pod["connected_device_count"]
                )
                if existing["name"] in {existing["model"], existing["id"], "Plume Pod"}:
                    existing["name"] = pod["name"]
                continue
            unique.append(pod)
            for value in identifiers:
                seen[value] = pod
        return unique

    @staticmethod
    def _device(row: dict, pod_names: dict[str, str]) -> dict:
        pod_ref = str(_value(
            row, "nodeId", "connectedNodeId", "parentNodeId", "mesh.nodeId", "node.id",
            "connection.nodeId", "connection.node.id", "wlan.nodeId", "wlan.node.id",
            "apId", "accessPointId", "bssid",
            default="",
        ))
        pod_name = _scalar_text(_value(
            row, "nodeName", "connectedNodeName", "podName", "node.nickname",
            "connectedNode.nickname", "connection.nodeName", "wlan.nodeName", default=""
        ))
        if not pod_name and pod_ref:
            normalized_ref = "".join(ch for ch in pod_ref if ch.isalnum()).lower()
            pod_name = pod_names.get(normalized_ref, "")
        if not pod_name:
            # Plume response versions use several different nested connection
            # shapes. Match any returned scalar identifier against pod aliases.
            for candidate in _recursive_values(row):
                normalized = "".join(ch for ch in candidate if ch.isalnum()).lower()
                if normalized in pod_names:
                    pod_name = pod_names[normalized]
                    break
        manufacturer = _scalar_text(_value(
            row, "manufacturer", "manufacturer.brand", "vendor", "kind.brand",
            "kind.manufacturer", default=""
        ))
        if not manufacturer:
            manufacturer = _scalar_text(_recursive_key(row.get("kind", {}), {"brand", "manufacturer"}))
        device_type = _scalar_text(_value(
            row, "deviceType", "type", "kind.category", "kind.type", default=""
        ))
        connection_type = _scalar_text(_value(
            row, "connectionType", "medium", "connection.type", "wlan.connectionType",
            default="wireless"
        )) or "wireless"
        wifi_band = _band_text(_value(
            row, "band", "wifiBand", "freqBand", "connection.band", "wlan.band",
            "wlan.frequencyBand", default=""
        ))
        return {
            "id": str(_value(row, "id", "deviceId", "mac", "macAddress", default="")),
            "name": str(_value(row, "nickname", "name", "deviceName", "hostname", default="Unknown device")),
            "manufacturer": manufacturer,
            "device_type": device_type,
            "mac_address": _mac(_value(row, "mac", "macAddress", "id")),
            "ip_address": str(_value(row, "ipv4", "ipv4Address", "ip", "ipAddress", "network.ipv4", default="")),
            "connection_type": connection_type,
            "wifi_band": wifi_band,
            "pod_name": pod_name or "Unknown",
            "status": _status(row),
            "signal_strength": _signal(row),
            "signal_timestamp": "",
            "signal_is_current": False,
            "last_seen": _value(row, "lastSeenAt", "lastSeen", "updatedAt", default=""),
            "raw": row,
        }

    @staticmethod
    def _speed_test(row: dict) -> dict:
        download = _number(_value(
            row, "download", "downloadMbps", "downloadSpeed", "downloadSpeedMbps",
            "downloadRate", "downlink", "downlinkMbps", "rx", "results.download",
            "result.download", "speed.download",
            default=None,
        ))
        upload = _number(_value(
            row, "upload", "uploadMbps", "uploadSpeed", "uploadSpeedMbps",
            "uploadRate", "uplink", "uplinkMbps", "tx", "results.upload",
            "result.upload", "speed.upload",
            default=None,
        ))
        if download is None:
            download = _number(_recursive_key(
                row, {"download", "downloadmbps", "downloadspeed", "downloadspeedmbps", "downloadrate", "downlink", "downlinkmbps", "rx"}
            ))
        if upload is None:
            upload = _number(_recursive_key(
                row, {"upload", "uploadmbps", "uploadspeed", "uploadspeedmbps", "uploadrate", "uplink", "uplinkmbps", "tx"}
            ))
        return {
            "request_id": _scalar_text(_value(row, "requestId", "id", "speedTestId")),
            "status": _scalar_text(_value(
                row, "status", "state", "testStatus", "result.status", default="complete"
            )).lower(),
            "download": download,
            "upload": upload,
            "latency": _integer(_value(
                row, "latency", "latencyMs", "rtt", "ping", "results.latency",
                "result.latency", default=None,
            )),
            "tested_at": _scalar_text(_value(
                row, "completedAt", "createdAt", "timestamp", "testedAt", "date", "startedAt"
            )),
        }

    @staticmethod
    def _has_speed_result(result: dict) -> bool:
        return result["download"] is not None or result["upload"] is not None
