from .client import BandwidthClient


class OrderingService:
    def __init__(self, client: BandwidthClient):
        self.client = client

    @property
    def account_id(self):
        return self.client.settings.bandwidth_account_id


    async def list(self, page: int = 1, size: int = 100):
        return await self.client.request(
            "GET",
            f"/accounts/{self.account_id}/orders",
            params={"page": page, "size": size},
        )

    async def create_existing_number_order(self, site_id, phone_numbers, name="Portal number order"):
        payload = {
            "CustomerOrderId": f"portal-{site_id}",
            "Name": name,
            "SiteId": int(site_id),
            "PartialAllowed": True,
            "ExistingTelephoneNumberOrderType": {
                "TelephoneNumberList": {
                    "TelephoneNumber": phone_numbers,
                }
            },
        }
        return await self.client.request(
            "POST", f"/accounts/{self.account_id}/orders", json_body=payload
        )
