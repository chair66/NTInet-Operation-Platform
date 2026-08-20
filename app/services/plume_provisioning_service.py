from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from app.providers.plume.client import PlumeClient, PlumeError, plume_client


def _object(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        for key in ("data", "customer", "location", "node", "result"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return payload
    return {}


def _identifier(payload: Any, *names: str) -> str:
    item = _object(payload)
    if isinstance(item.get("data"), (str, int)):
        return str(item["data"]).strip()
    return next((str(item.get(name) or "").strip() for name in names if item.get(name)), "")


@dataclass(slots=True)
class PlumeProvisioningService:
    """Explicit Plume write operations. Callers must enforce staff-only access."""

    client: PlumeClient = plume_client

    def node_inventory(self, serial_number: str) -> dict[str, Any]:
        serial = serial_number.strip()
        if not serial:
            raise ValueError("Enter a pod or gateway serial number.")
        return _object(self.client.get(f"/Partners/nodes/{quote(serial, safe='')}"))

    def register_customer(
        self, *, account_id: str, name: str, email: str, partner_id: str
    ) -> dict[str, Any]:
        account = account_id.strip()
        if len(account) < 6:
            raise ValueError("Plume account ID must contain at least 6 characters.")
        if not name.strip():
            raise ValueError("Customer name is required.")
        if email.strip() and "@" not in email:
            raise ValueError("Enter a valid customer email address.")
        if not partner_id.strip():
            raise ValueError("The pod inventory response did not include a partner ID.")
        body = {
            "accountId": account,
            "name": name.strip(),
            "partnerId": partner_id.strip(),
        }
        if email.strip():
            body["email"] = email.strip()
        result = self.client.post("/Customers/register", json_body=body)
        customer_id = _identifier(result, "id", "customerId")
        if not customer_id:
            raise ValueError("Plume created the customer but did not return its customer ID.")
        return {**_object(result), "id": customer_id}

    def create_location(self, *, customer_id: str, name: str, service_id: str = "") -> dict[str, Any]:
        form = {"name": name.strip() or "Primary Location"}
        if service_id.strip():
            form["serviceId"] = service_id.strip()
        result = self.client.post(
            f"/Customers/{quote(customer_id, safe='')}/locations", form_data=form
        )
        location_id = _identifier(result, "id", "locationId")
        if not location_id:
            raise ValueError("Plume created the location but did not return its location ID.")
        return {**_object(result), "id": location_id}

    def claim_node(
        self,
        *,
        customer_id: str,
        location_id: str,
        serial_number: str,
        nickname: str = "",
    ) -> Any:
        form = {"serialNumber": serial_number.strip()}
        if nickname.strip():
            form["nickname"] = nickname.strip()
        return self.client.post(
            f"/Customers/{quote(customer_id, safe='')}/locations/"
            f"{quote(location_id, safe='')}/nodes",
            form_data=form,
        )

    def rename_node(
        self, *, customer_id: str, location_id: str, node_id: str, nickname: str
    ) -> Any:
        if not nickname.strip():
            raise ValueError("Pod name is required.")
        return self.client.request(
            "PUT",
            f"/Customers/{quote(customer_id, safe='')}/locations/"
            f"{quote(location_id, safe='')}/nodes/{quote(node_id, safe='')}",
            form_data={"nickname": nickname.strip(), "emitMessage": "false"},
        )

    def unclaim_node(
        self, *, customer_id: str, location_id: str, node_id: str
    ) -> Any:
        try:
            return self.client.delete(
                f"/Customers/{quote(customer_id, safe='')}/locations/"
                f"{quote(location_id, safe='')}/nodes/{quote(node_id, safe='')}",
                form_data={"preservePackId": "true", "removeAccountId": "false"},
            )
        except PlumeError as exc:
            # DELETE is idempotent from NOP's perspective. Some Plume clouds
            # complete the unclaim but respond after the node has disappeared,
            # producing this exact 404. The requested final state is satisfied.
            if exc.status_code == 404 and "node not found on this location" in str(exc).lower():
                return {"alreadyAbsent": True, "nodeId": node_id}
            raise
