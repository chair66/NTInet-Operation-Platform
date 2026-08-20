from __future__ import annotations

from typing import Any

from .client import NetSapiensClient


class NetSapiensDomains:
    """NetSapiens domain API operations."""

    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    def list(self, reseller: str) -> list[dict[str, Any]]:
        """Return all domains visible for a reseller.

        NetSapiens deployments can wrap collections differently, so this
        method accepts the common list, data, domains, and items response
        shapes while keeping the service layer independent of those details.
        """
        result = self.client.request(
            "GET",
            "/domains",
            params={"reseller": reseller, "limit": 1000},
        )

        if isinstance(result, list):
            return [row for row in result if isinstance(row, dict)]

        if isinstance(result, dict):
            for key in ("data", "domains", "items", "results"):
                rows = result.get(key)
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)]

            # Some NetSapiens responses return one domain object directly.
            if any(key in result for key in ("domain", "domain_name", "name")):
                return [result]

        return []

    def get(self, domain_name: str):
        return self.client.request("GET", f"/domains/{domain_name}")

    def create(self, reseller: str, payload: dict):
        body = dict(payload)
        body["reseller"] = reseller
        return self.client.request("POST", "/domains", json=body)

    def update(self, domain_name: str, payload: dict):
        return self.client.request("PUT", f"/domains/{domain_name}", json=payload)

    def delete(self, domain_name: str):
        return self.client.request("DELETE", f"/domains/{domain_name}")
