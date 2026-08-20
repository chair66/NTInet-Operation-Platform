from __future__ import annotations

from typing import Any
from urllib.parse import quote
from uuid import uuid4

from .client import NetSapiensClient, NetSapiensError


class NetSapiensEmergencyAddresses:
    """Validate addresses and manage legacy-911 callback-number endpoints."""

    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    @staticmethod
    def _body(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "emergency-address-id": str(payload.get("emergency_address_id") or "").strip(),
            "address-name": str(payload.get("address_name") or "Residential Service Address").strip(),
            "caller-name": str(payload.get("caller_name") or "").strip(),
            "address-line-1": str(payload.get("address_line_1") or "").strip(),
            "address-line-2": str(payload.get("address_line_2") or "").strip(),
            "address-country-abbreviation": str(payload.get("country") or "US").strip().upper(),
            "address-state-province-abbreviation": str(payload.get("state") or "").strip().upper(),
            "address-city": str(payload.get("city") or "").strip(),
            "address-postal-code": str(payload.get("postal_code") or "").strip(),
            "address-location-description": str(
                payload.get("location_description") or "Residential service address"
            ).strip(),
        }

    @staticmethod
    def _object(result: Any) -> dict[str, Any]:
        if isinstance(result, list):
            return next((row for row in result if isinstance(row, dict)), {})
        if not isinstance(result, dict):
            return {}
        for key in ("data", "address", "result"):
            value = result.get(key)
            if isinstance(value, dict):
                return value
            if isinstance(value, list):
                return next((row for row in value if isinstance(row, dict)), {})
        return result

    @classmethod
    def _rows(cls, result: Any) -> list[dict[str, Any]]:
        if isinstance(result, list):
            return [row for row in result if isinstance(row, dict)]
        if not isinstance(result, dict):
            return []
        for key in ("data", "addresses", "items", "results", "records"):
            value = result.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
            if isinstance(value, dict):
                nested = cls._rows(value)
                if nested:
                    return nested
        if cls._field(result, "emergency-address-id") or cls._field(result, "address-line-1"):
            return [result]
        return []

    @staticmethod
    def _field(payload: dict[str, Any], name: str, default: Any = "") -> Any:
        wanted = "".join(ch for ch in name.lower() if ch.isalnum())
        for key, value in payload.items():
            normalized = "".join(ch for ch in str(key).lower() if ch.isalnum())
            if normalized == wanted and value not in (None, ""):
                return value
        return default

    @classmethod
    def _assignment_body(cls, payload: dict[str, Any], *, include_id: bool) -> dict[str, Any]:
        fields = (
            "address-name", "caller-name", "address-line-1", "address-line-2",
            "address-city", "address-state-province-abbreviation",
            "address-postal-code", "address-country-abbreviation",
            "address-location-description", "ip-address-public",
            "address-formatted-pidflo", "carrier",
        )
        body = {field: cls._field(payload, field) for field in fields}
        if not body["carrier"]:
            body["carrier"] = cls._field(payload, "address-provisioned-carrier-name")
        if include_id:
            body["emergency-address-id"] = cls._field(payload, "emergency-address-id")
        return body

    def validate(self, domain: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = self._body(payload)
        if not body["emergency-address-id"]:
            body["emergency-address-id"] = f"a-{uuid4().hex}"
        required = {
            "Caller name": body["caller-name"],
            "Address": body["address-line-1"],
            "City": body["address-city"],
            "State": body["address-state-province-abbreviation"],
            "ZIP": body["address-postal-code"],
        }
        missing = [label for label, value in required.items() if not value]
        if missing:
            raise ValueError(f"Legacy 911 address is missing: {', '.join(missing)}")
        result = self.client.request(
            "POST",
            f"/domains/{quote(domain, safe='')}/addresses/validate",
            json=body,
        )
        validated = dict(body)
        validated.update(self._object(result))
        validated["emergency-address-id"] = str(
            self._field(validated, "emergency-address-id", body["emergency-address-id"])
        ).strip()
        # The final resource is still a Legacy 911 callback endpoint. The API
        # requires the validation result as address input when no location_id
        # is supplied, so retain it solely as the endpoint write token.
        pidflo = self._field(validated, "address-formatted-pidflo")
        if not pidflo:
            raise ValueError(
                "DigiCloud validated the address but did not return the address input "
                "required to save the legacy 911 endpoint."
            )
        return validated

    @classmethod
    def address_view(cls, row: dict[str, Any] | None) -> dict[str, Any]:
        source = row if isinstance(row, dict) else {}
        provisioned_carrier = str(
            cls._field(source, "address-provisioned-carrier-name")
            or cls._field(source, "carrier")
            or ""
        ).strip()
        carrier_state = provisioned_carrier.lower().replace("_", "-")
        carrier_provisioned = carrier_state not in {
            "", "none", "null", "n/a", "unknown", "pending", "unprovisioned",
            "not-provisioned", "false", "no",
        }
        return {
            "emergency_address_id": str(cls._field(source, "emergency-address-id") or "").strip(),
            "caller_name": str(cls._field(source, "caller-name") or "").strip(),
            "address_line_1": str(cls._field(source, "address-line-1") or "").strip(),
            "address_line_2": str(cls._field(source, "address-line-2") or "").strip(),
            "city": str(cls._field(source, "address-city") or "").strip(),
            "state": str(cls._field(source, "address-state-province-abbreviation") or "").strip(),
            "postal_code": str(cls._field(source, "address-postal-code") or "").strip(),
            "country": str(cls._field(source, "address-country-abbreviation") or "US").strip(),
            "provisioned_carrier": provisioned_carrier,
            "carrier_provisioned": carrier_provisioned,
            "endpoint_owner": str(cls._field(source, "user") or "").strip(),
        }

    @staticmethod
    def _digits(value: Any) -> str:
        return "".join(ch for ch in str(value or "") if ch.isdigit())

    @classmethod
    def endpoint_callback_number(cls, row: dict[str, Any]) -> str:
        for field in ("address-callback-number", "endpoint"):
            digits = cls._digits(cls._field(row, field))
            if digits:
                return digits[-10:] if len(digits) >= 10 else digits
        owner = str(cls._field(row, "user") or "").strip().lower().replace("-", "_")
        if owner == "address_endpoint":
            digits = cls._digits(cls._field(row, "emergency-address-id"))
            if digits:
                return digits[-10:] if len(digits) >= 10 else digits
        return ""

    def list_endpoints(self, domain: str) -> list[dict[str, Any]]:
        try:
            result = self.client.request(
                "GET",
                f"/domains/{quote(domain, safe='')}/addresses/endpoints",
                params={"limit": 1000},
            )
        except NetSapiensError as exc:
            if "HTTP 404" in str(exc):
                return []
            raise
        return self._rows(result)

    def endpoint_for_did(self, domain: str, did: str) -> dict[str, Any]:
        wanted = self._digits(did)[-10:]
        if len(wanted) != 10:
            return {}
        for row in self.list_endpoints(domain):
            if self.endpoint_callback_number(row) == wanted:
                view = self.address_view(row)
                view["callback_number"] = wanted
                return view
        return {}

    def list_domain_addresses(self, domain: str) -> list[dict[str, Any]]:
        try:
            result = self.client.request(
                "GET",
                f"/domains/{quote(domain, safe='')}/addresses",
                params={"limit": 1000},
            )
        except NetSapiensError as exc:
            if "HTTP 404" in str(exc):
                return []
            raise
        return self._rows(result)

    def domain_address_by_id(
        self,
        domain: str,
        emergency_address_id: str,
    ) -> dict[str, Any]:
        wanted = str(emergency_address_id or "").strip()
        if not wanted:
            return {}
        for row in self.list_domain_addresses(domain):
            if str(self._field(row, "emergency-address-id") or "").strip() == wanted:
                view = self.address_view(row)
                view["emergency_address_id"] = wanted
                return view
        return {}

    def user_address_by_id(
        self,
        domain: str,
        user: str,
        emergency_address_id: str,
    ) -> dict[str, Any]:
        wanted = str(emergency_address_id or "").strip()
        if not wanted:
            return {}
        try:
            result = self.client.request(
                "GET",
                (
                    f"/domains/{quote(domain, safe='')}/users/"
                    f"{quote(user, safe='')}/addresses/{quote(wanted, safe='')}"
                ),
            )
        except NetSapiensError as exc:
            if "HTTP 404" in str(exc):
                return {}
            raise
        row = self._object(result)
        if not row:
            return {}
        returned_id = str(self._field(row, "emergency-address-id") or wanted).strip()
        if returned_id != wanted:
            return {}
        view = self.address_view(row)
        view["emergency_address_id"] = wanted
        return view

    def create_user_address(
        self,
        domain: str,
        user: str,
        validated: dict[str, Any],
    ) -> dict[str, Any]:
        return self._object(self.client.request(
            "POST",
            (
                f"/domains/{quote(domain, safe='')}/users/"
                f"{quote(user, safe='')}/addresses"
            ),
            json=self._domain_address_body(validated, include_id=True),
        ))

    def update_user_address(
        self,
        domain: str,
        user: str,
        emergency_address_id: str,
        validated: dict[str, Any],
    ) -> dict[str, Any]:
        return self._object(self.client.request(
            "PUT",
            (
                f"/domains/{quote(domain, safe='')}/users/"
                f"{quote(user, safe='')}/addresses/"
                f"{quote(emergency_address_id, safe='')}"
            ),
            json=self._domain_address_body(validated, include_id=False),
        ))

    def create_domain_address(
        self,
        domain: str,
        validated: dict[str, Any],
    ) -> dict[str, Any]:
        return self._object(self.client.request(
            "POST",
            f"/domains/{quote(domain, safe='')}/addresses",
            json=self._domain_address_body(validated, include_id=True),
        ))

    def update_domain_address(
        self,
        domain: str,
        emergency_address_id: str,
        validated: dict[str, Any],
    ) -> dict[str, Any]:
        return self._object(self.client.request(
            "PUT",
            (
                f"/domains/{quote(domain, safe='')}/addresses/"
                f"{quote(emergency_address_id, safe='')}"
            ),
            json=self._domain_address_body(validated, include_id=False),
        ))

    @classmethod
    def _domain_address_body(
        cls,
        validated: dict[str, Any],
        *,
        include_id: bool,
    ) -> dict[str, Any]:
        body = cls._assignment_body(validated, include_id=include_id)
        carrier = str(
            cls._field(validated, "address-provisioned-carrier-name")
            or cls._field(validated, "carrier")
            or ""
        ).strip()
        if carrier:
            body["carrier"] = carrier
        return body

    @classmethod
    def _endpoint_body(
        cls,
        did: str,
        validated: dict[str, Any],
        *,
        include_callback: bool,
    ) -> dict[str, Any]:
        body = cls._assignment_body(validated, include_id=False)
        # This DigiCloud build accepts the validation result only as its native
        # JSON object. It is endpoint address input, not a Dynamic 911 record.
        body.pop("ip-address-public", None)
        carrier = str(
            cls._field(validated, "address-provisioned-carrier-name")
            or cls._field(validated, "carrier")
            or ""
        ).strip()
        if carrier:
            body["carrier"] = carrier
        if include_callback:
            body["address-callback-number"] = cls._digits(did)[-10:]
        return body

    def create_endpoint(
        self,
        domain: str,
        did: str,
        validated: dict[str, Any],
    ) -> dict[str, Any]:
        return self._object(self.client.request(
            "POST",
            f"/domains/{quote(domain, safe='')}/addresses/endpoints",
            json=self._endpoint_body(
                did,
                validated,
                include_callback=True,
            ),
        ))

    def update_endpoint(
        self,
        domain: str,
        did: str,
        validated: dict[str, Any],
    ) -> dict[str, Any]:
        callback_number = self._digits(did)[-10:]
        return self._object(self.client.request(
            "PUT",
            (
                f"/domains/{quote(domain, safe='')}/addresses/endpoints/"
                f"{quote(callback_number, safe='')}"
            ),
            json=self._endpoint_body(
                callback_number,
                validated,
                include_callback=False,
            ),
        ))
