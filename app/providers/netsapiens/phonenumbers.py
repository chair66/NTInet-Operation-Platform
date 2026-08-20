from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .client import NetSapiensClient


def _api_tn(phonenumber: str) -> str:
    digits = "".join(ch for ch in str(phonenumber) if ch.isdigit())
    if len(digits) == 10:
        return "1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return digits
    return digits


class NetSapiensPhoneNumbers:
    """NetSapiens phone-number inventory and domain assignment operations."""

    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    @staticmethod
    def _rows(result: Any) -> list[dict[str, Any]]:
        """Normalize direct and nested NetSapiens collection envelopes."""
        if isinstance(result, list):
            return [row for row in result if isinstance(row, dict)]
        if not isinstance(result, dict):
            return []
        for key in ("data", "phonenumbers", "phone_numbers", "items", "results", "records"):
            value = result.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
            if isinstance(value, dict):
                nested = NetSapiensPhoneNumbers._rows(value)
                if nested:
                    return nested
        if any(key in result for key in ("phonenumber", "phone_number", "telephone_number")):
            return [result]
        return []

    def list(self, reseller: str) -> list[dict[str, Any]]:
        """Return phone numbers visible to a reseller.

        NetSapiens v2 exposes the reseller/system inventory at
        ``GET /phonenumbers``. Deployments may return the collection directly
        or wrap it in a common envelope, so normalize those response shapes
        here instead of leaking provider details into the service layer.
        """
        result = self.client.request(
            "GET",
            "/phonenumbers",
            params={"reseller": reseller, "limit": 10000},
        )

        return self._rows(result)

    def list_for_domain(self, domain: str) -> list[dict[str, Any]]:
        """Return the live phone-number routes configured in one domain."""
        result = self.client.request(
            "GET",
            f"/domains/{quote(domain, safe='')}/phonenumbers",
            params={"limit": 10000},
        )
        return self._rows(result)


    def get_for_domain(self, domain: str, phonenumber: str) -> dict[str, Any]:
        result = self.client.request(
            "GET",
            f"/domains/{quote(domain, safe='')}/phonenumbers/{_api_tn(phonenumber)}",
        )
        if isinstance(result, list):
            return next((row for row in result if isinstance(row, dict)), {})
        return result if isinstance(result, dict) else {}

    def add_to_domain(
        self,
        domain: str,
        phonenumber: str,
        *,
        destination_user: str,
        description: str = "",
        treatment: str = "available",
        enabled: bool = True,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        body = dict(payload or {})
        body["phonenumber"] = _api_tn(phonenumber)
        body["enabled"] = "yes" if enabled else "no"
        body["dial-rule-application"] = treatment
        body["dial-rule-translation-destination-user"] = destination_user
        body["dial-rule-translation-destination-host"] = domain
        if description:
            body["dial-rule-description"] = description
        return self.client.request(
            "POST",
            f"/domains/{quote(domain, safe='')}/phonenumbers",
            json=body,
        )

    def update_in_domain(
        self,
        domain: str,
        phonenumber: str,
        *,
        destination_user: str,
        description: str = "",
        treatment: str = "available",
        enabled: bool = True,
    ) -> Any:
        body: dict[str, Any] = {
            "enabled": "yes" if enabled else "no",
            "dial-rule-application": treatment,
            "dial-rule-translation-destination-user": destination_user,
            "dial-rule-translation-destination-host": domain,
        }
        if description:
            body["dial-rule-description"] = description
        return self.client.request(
            "PUT",
            f"/domains/{quote(domain, safe='')}/phonenumbers/{_api_tn(phonenumber)}",
            json=body,
        )

    def remove_from_domain(self, domain: str, phonenumber: str) -> Any:
        return self.client.request(
            "DELETE",
            f"/domains/{quote(domain, safe='')}/phonenumbers/{_api_tn(phonenumber)}",
        )
