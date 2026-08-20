from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .client import BandwidthClient
from app.services.phone_numbers import normalize_e164


class PortingService:
    def __init__(self, client: BandwidthClient):
        self.client = client

    @property
    def account_id(self):
        return self.client.settings.bandwidth_account_id

    async def list(self, page: int = 1, size: int = 300):
        return await self.client.request(
            "GET",
            f"/accounts/{self.account_id}/portins",
            params={"page": page, "size": size},
        )

    async def check_portability(self, phone_numbers: list[str]):
        """Check portability with Bandwidth OnePort.

        OnePort returns normalized portable groups with the losing carrier,
        port type, phone-number type, rate center, document requirements, and
        Bandwidth's earliest estimated port date. Telephone numbers must be
        supplied in E.164 format.
        """
        normalized = list(dict.fromkeys(normalize_e164(number) for number in phone_numbers))
        return await self.client.request(
            "POST",
            f"/accounts/{self.account_id}/porting/portability/phoneNumbers",
            json_body={"phoneNumbers": normalized},
        )

    async def list_portouts(
        self,
        page: int = 1,
        size: int = 100,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        """List port-out orders belonging to this Bandwidth account.

        Port-out orders shown in the Bandwidth portal are exposed by the
        ``/portouts`` resource, not the gaining-carrier ``/lsrorders``
        resource. Bandwidth's list operation is date-range based, so use a
        five-year window by default while still allowing callers to override
        it later.
        """
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=365 * 5))
        return await self.client.request(
            "GET",
            f"/accounts/{self.account_id}/portouts",
            params={
                "startdate": start_date.isoformat(),
                "enddate": end_date.isoformat(),
                "page": page,
                "size": size,
            },
        )

    async def get_portout(self, order_id):
        return await self.client.request(
            "GET", f"/accounts/{self.account_id}/portouts/{order_id}"
        )

    async def get(self, order_id):
        return await self.client.request(
            "GET", f"/accounts/{self.account_id}/portins/{order_id}"
        )

    async def create(self, payload):
        return await self.client.request(
            "POST", f"/accounts/{self.account_id}/portins", json_body=payload
        )

    async def submit_draft(self, order_id, payload):
        submitted_payload = dict(payload or {})
        submitted_payload["processingStatus"] = "SUBMITTED"
        return await self.client.request(
            "PUT",
            f"/accounts/{self.account_id}/portins/{order_id}",
            json_body=submitted_payload,
        )

    async def cancel(self, order_id):
        return await self.client.request(
            "DELETE", f"/accounts/{self.account_id}/portins/{order_id}"
        )

