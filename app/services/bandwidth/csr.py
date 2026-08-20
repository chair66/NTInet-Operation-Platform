from .client import BandwidthClient


class CSRService:
    def __init__(self, client: BandwidthClient):
        self.client = client

    @property
    def account_id(self):
        return self.client.settings.bandwidth_account_id

    async def list(self):
        return await self.client.request("GET", f"/accounts/{self.account_id}/csrs")

    async def create(self, payload):
        return await self.client.request(
            "POST", f"/accounts/{self.account_id}/csrs", json_body=payload
        )
