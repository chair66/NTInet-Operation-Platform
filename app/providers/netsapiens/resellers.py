from __future__ import annotations

from typing import Any

from .client import NetSapiensClient


class NetSapiensResellers:
    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    def list(self) -> list[dict[str, Any]]:
        data = self.client.request("GET", "/resellers")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("data", "items", "resellers"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return []

    def get(self, reseller: str) -> dict[str, Any] | None:
        target = str(reseller or "").strip()
        if not target:
            return None
        # Some NetSapiens deployments do not expose a single-reseller GET.
        # The collection endpoint is reliable and avoids treating a route-level
        # 404 as proof that the reseller does not exist.
        for item in self.list():
            if str(item.get("reseller") or "").strip().casefold() == target.casefold():
                return item
        return None

    def create(self, reseller: str, description: str = "") -> Any:
        payload = {
            "reseller": str(reseller or "").strip(),
            "description": str(description or "").strip(),
        }
        return self.client.request("POST", "/resellers", json=payload)

    def update(self, reseller: str, description: str = "") -> Any:
        return self.client.request(
            "PUT",
            f"/resellers/{str(reseller or '').strip()}",
            json={"description": str(description or "").strip()},
        )
