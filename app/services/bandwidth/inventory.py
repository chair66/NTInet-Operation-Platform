from __future__ import annotations

from typing import Any
import xml.etree.ElementTree as ET

from .client import BandwidthClient


class InventoryService:
    def __init__(self, client: BandwidthClient):
        self.client = client

    @property
    def account_id(self) -> str:
        return self.client.settings.bandwidth_account_id

    async def list_sites(self) -> list[dict[str, Any]]:
        data = await self.client.request("GET", f"/accounts/{self.account_id}/sites")
        raw_sites = _items(data, "subAccounts", "sites", "Sites", "Site")
        return [_normalise_site(site) for site in raw_sites]

    async def site_total(self, site_id: int | str) -> int:
        data = await self.client.request(
            "GET", f"/accounts/{self.account_id}/sites/{site_id}/totaltns"
        )
        return _extract_count(data)

    async def list_locations(self, site_id: int | str) -> list[dict[str, Any]]:
        data = await self.client.request(
            "GET", f"/accounts/{self.account_id}/sites/{site_id}/sippeers"
        )
        raw_locations = _items(
            data,
            "sipPeers",
            "sippeers",
            "locations",
            "SipPeers",
            "SipPeer",
        )
        return [_normalise_location(location) for location in raw_locations]

    async def list_numbers(self, site_id, location_id, page=None, size=50) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"size": size}
        if page:
            params["page"] = page
        data = await self.client.request(
            "GET",
            f"/accounts/{self.account_id}/sites/{site_id}/sippeers/{location_id}/tns",
            params=params,
        )
        return _normalise_numbers(data)

    async def search_available_numbers(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        params = {k: v for k, v in query.items() if v not in (None, "")}
        params.setdefault("enableTNDetail", "true")
        data = await self.client.request(
            "GET", f"/accounts/{self.account_id}/availableNumbers", params=params
        )
        return _normalise_available_numbers(data)

    async def move_number(self, telephone_number: str, site_id: int, location_id: int, customer_order_id: str):
        root = ET.Element("MoveTnsOrder")
        ET.SubElement(root, "CustomerOrderId").text = customer_order_id
        ET.SubElement(root, "SiteId").text = str(site_id)
        ET.SubElement(root, "SipPeerId").text = str(location_id)
        numbers = ET.SubElement(root, "TelephoneNumbers")
        ET.SubElement(numbers, "TelephoneNumber").text = telephone_number.lstrip("+")
        body = ET.tostring(root, encoding="unicode")
        return await self.client.request(
            "POST",
            f"/accounts/{self.account_id}/moveTns",
            content=body,
            content_type="application/xml",
        )


def _items(data: Any, *keys: str) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    # Try explicit container names first.
    for key in keys:
        value = _get_ci(data, key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _single_or_list(value)
            if nested:
                return nested

    # Bandwidth responses sometimes add a one-element response wrapper.
    for value in data.values():
        if isinstance(value, dict):
            nested = _items(value, *keys)
            if nested:
                return nested
    return []


def _normalise_site(site: Any) -> dict[str, Any]:
    if not isinstance(site, dict):
        return {"id": "", "name": str(site), "description": ""}
    result = dict(site)
    result["id"] = _first(site, "id", "siteId", "Id", "SiteId")
    result["name"] = _first(site, "name", "siteName", "Name", "SiteName") or "Unnamed sub account"
    result["description"] = _first(site, "description", "Description") or ""
    return result


def _normalise_location(location: Any) -> dict[str, Any]:
    if not isinstance(location, dict):
        return {"id": "", "name": str(location)}
    result = dict(location)
    result["id"] = _first(
        location, "id", "peerId", "sipPeerId", "locationId", "Id", "PeerId", "SipPeerId"
    )
    result["name"] = _first(
        location, "name", "peerName", "locationName", "Name", "PeerName", "LocationName"
    ) or f"Location {result['id']}"
    return result


def _normalise_numbers(data: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item, inherited in _walk_number_records(data):
        number = _number_value(item)
        if not number or number in seen:
            continue
        seen.add(number)
        row = dict(inherited)
        if isinstance(item, dict):
            row.update(item)
        row["phoneNumber"] = number
        row["callForward"] = _first(row, "callForward", "CallForward") or ""
        row["numberFormat"] = _first(row, "numberFormat", "NumberFormat") or ""
        row["rewriteUser"] = _first(row, "rewriteUser", "RewriteUser") or ""
        results.append(row)
    return results


def _normalise_available_numbers(data: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item, inherited in _walk_number_records(data):
        number = _number_value(item)
        if not number or number in seen:
            continue
        seen.add(number)
        row = dict(inherited)
        if isinstance(item, dict):
            row.update(item)
        row["phoneNumber"] = number
        row["numberType"] = _first(row, "phoneNumberType", "numberType", "NumberType") or "Local"
        row["rateCenter"] = _first(row, "rateCenter", "RateCenter", "ratecenter") or ""
        row["state"] = _first(row, "state", "State") or ""
        row["city"] = _first(row, "city", "City") or ""
        results.append(row)
    return results


def _walk_number_records(data: Any, inherited: dict[str, Any] | None = None):
    """Yield number-bearing records while preserving parent metadata."""
    inherited = dict(inherited or {})
    if isinstance(data, (str, int)):
        value = str(data).strip()
        digits = value.lstrip("+").replace("-", "").replace(" ", "")
        if digits.isdigit() and 7 <= len(digits) <= 15:
            yield value, inherited
        return
    if isinstance(data, list):
        for item in data:
            yield from _walk_number_records(item, inherited)
        return
    if not isinstance(data, dict):
        return

    metadata = dict(inherited)
    for key, value in data.items():
        if str(key).casefold() in {
            "ratecenter", "state", "city", "phonenumbertype", "numbertype",
            "lata", "zip", "zipcode", "countrycodea3"
        } and not isinstance(value, (dict, list)):
            metadata[str(key)] = value

    direct = _number_value(data)
    if direct:
        yield data, metadata

    for value in data.values():
        if isinstance(value, (dict, list, str, int)):
            yield from _walk_number_records(value, metadata)


def _number_value(item: Any) -> str | None:
    if isinstance(item, (str, int)):
        value = str(item).strip()
        digits = value.lstrip("+").replace("-", "").replace(" ", "")
        return value if digits.isdigit() and 7 <= len(digits) <= 15 else None
    if not isinstance(item, dict):
        return None
    value = _first(
        item, "phoneNumber", "telephoneNumber", "fullNumber", "tn",
        "PhoneNumber", "TelephoneNumber", "FullNumber", "TN"
    )
    if isinstance(value, (str, int)):
        return str(value).strip()
    return None


def _extract_count(data: Any) -> int:
    if isinstance(data, bool):
        return 0
    if isinstance(data, int):
        return data
    if isinstance(data, str) and data.strip().isdigit():
        return int(data.strip())
    if isinstance(data, list):
        for value in data:
            count = _extract_count(value)
            if count:
                return count
        return 0
    if isinstance(data, dict):
        preferred = (
            "totalTnCount",
            "totalTNCount",
            "totalPhoneNumberCount",
            "telephoneNumberCount",
            "tnCount",
            "count",
            "total",
            "TotalCount",
            "TelephoneNumberCount",
        )
        for key in preferred:
            value = _get_ci(data, key)
            if value is not None:
                count = _extract_count(value)
                if count or str(value).strip() == "0":
                    return count
        for value in data.values():
            count = _extract_count(value)
            if count:
                return count
    return 0


def _first(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = _get_ci(data, key)
        if value not in (None, ""):
            return value
    return None


def _get_ci(data: dict[str, Any], key: str) -> Any:
    target = key.casefold()
    for actual_key, value in data.items():
        if str(actual_key).casefold() == target:
            return value
    return None


def _single_or_list(value: dict[str, Any]) -> list[Any]:
    if len(value) == 1:
        only = next(iter(value.values()))
        if isinstance(only, list):
            return only
        if isinstance(only, (dict, str, int)):
            return [only]
    return []
