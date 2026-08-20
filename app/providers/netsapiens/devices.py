from __future__ import annotations

from urllib.parse import quote

from .client import NetSapiensClient


class NetSapiensDevices:
    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    @staticmethod
    def _path(domain: str, user: str, device: str | None = None) -> str:
        path = f"/domains/{quote(domain, safe='')}/users/{quote(user, safe='')}/devices"
        if device is not None:
            path += f"/{quote(device, safe='')}"
        return path

    def list(self, domain: str, user: str) -> list[dict]:
        payload = self.client.request("GET", self._path(domain, user))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "devices", "items"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    def get(self, domain: str, user: str, device: str) -> dict:
        # Some deployed NetSapiens builds do not expose the device-specific
        # GET route and return "No Route Found [92]". Resolve the device
        # from the supported collection endpoint instead.
        target = str(device or "").strip().casefold()
        for row in self.list(domain, user):
            if not isinstance(row, dict):
                continue
            row_device = str(row.get("device") or "").strip().casefold()
            if row_device == target:
                return row
        return {}

    def create_manual(self, domain: str, user: str, payload: dict) -> dict:
        result = self.client.request(
            "POST", self._path(domain, user), params={"synchronous": "yes"}, json=payload
        )
        return result if isinstance(result, dict) else {"result": result}

    def update(self, domain: str, user: str, device: str, payload: dict) -> dict:
        # The released device-specific route does not document a synchronous
        # query parameter. Some NetSapiens builds return "No Route Found [92]"
        # when it is appended to this PUT, so use the exact OpenAPI route.
        result = self.client.request(
            "PUT", self._path(domain, user, device), json=payload
        )
        return result if isinstance(result, dict) else {"result": result}

    def delete(self, domain: str, user: str, device: str) -> dict:
        result = self.client.request(
            "DELETE", self._path(domain, user, device)
        )
        return result if isinstance(result, dict) else {"result": result}


class NetSapiensPhoneProvisioning:
    def __init__(self, client: NetSapiensClient | None = None) -> None:
        self.client = client or NetSapiensClient()

    def models(self) -> list[dict]:
        payload = self.client.request("GET", "/phones/models")
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "models", "items"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    def model_details(self, *, brand: str, model: str) -> dict:
        payload = self.client.request(
            "GET", "/phones/models", params={"brand": brand, "model": model}
        )
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list) and payload:
            return payload[0] if isinstance(payload[0], dict) else {}
        return {}


    def servers(self) -> list[dict]:
        payload = self.client.request("GET", "/phones/servers")
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "servers", "items"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    def get_phone(self, mac: str) -> dict:
        payload = self.client.request("GET", f"/phones/{quote(mac, safe='')}")
        return payload if isinstance(payload, dict) else {}

    def update_phone(self, *, mac: str, model: str, server: str, domain: str,
                     subscriber_name: str = "", transport: str = "udp", notes: str = "", overrides: str = "",
                     line_assignments: list[str] | None = None) -> dict:
        """Update an existing MAC inventory record through PUT /phones.

        NetSapiens documents the short phone-inventory field names for this
        operation. Both ``mac`` and ``model`` are required. Line assignments
        are supplied as ``device1`` through ``device8``.
        """
        payload = {
            "mac": mac,
            "model": model,
            "server": server,
            "subscriber_name": subscriber_name or "",
            "domain": domain,
            "transport": (transport or "udp").lower(),
            "notes": notes or "",
            "overrides": overrides or "",
        }
        if line_assignments is not None:
            for index in range(1, 9):
                value = ""
                if index <= len(line_assignments):
                    value = str(line_assignments[index - 1] or "").strip()
                payload[f"device{index}"] = value
                if index <= 6:
                    payload[f"line{index}_share"] = "no"
        result = self.client.request("PUT", "/phones", json=payload)
        return result if isinstance(result, dict) else {"result": result}

    def list_domain_phones(self, domain: str, *, limit: int = 1000) -> list[dict]:
        """Read the live DigiCloud MAC inventory assigned to one domain."""
        payload = self.client.request(
            "GET", f"/domains/{quote(domain, safe='')}/phones", params={"limit": limit}
        )
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "phones", "items"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    def list_phones(self, *, limit: int = 10000) -> list[dict]:
        payload = self.client.request("GET", "/phones", params={"limit": limit})
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "phones", "items"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    def delete_phone(self, mac: str) -> dict:
        # The OpenAPI schema defines removal as DELETE /phones with the MAC in
        # the JSON body. /phones/{mac} is GET-only on this API release.
        normalized = "".join(ch for ch in str(mac or "") if ch.isalnum()).upper()
        result = self.client.request(
            "DELETE", "/phones",
            json={"device-provisioning-mac-address": normalized},
        )
        return result if isinstance(result, dict) else {"result": result}

    def provision(self, *, mac: str, model: str, server: str, subscriber_name: str = "",
                  domain: str = "", transport: str = "udp", notes: str = "") -> dict:
        payload = {
            "mac": mac,
            "model": model,
            "server": server,
            "subscriber_name": subscriber_name,
            "domain": domain,
            "transport": (transport or "udp").lower(),
            "notes": notes or "",
        }
        result = self.client.request("POST", "/phones", params={"synchronous": "yes"}, json=payload)
        return result if isinstance(result, dict) else {"result": result}
