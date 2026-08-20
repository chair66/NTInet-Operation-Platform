from __future__ import annotations

from typing import Any

from app.services.platypus import PlatypusClient


class CustomerDirectory:
    """Customer-source boundary for Ticketing.

    Ticketing should depend on this service instead of demo/local billing data.
    Platypus is the live customer/rate/service source of record; NOP-owned ticket,
    job, estimate, and communications records can continue to reference the
    immutable Platypus customer id.
    """

    def __init__(self, client: PlatypusClient | None = None) -> None:
        self.client = client or PlatypusClient()

    async def search(self, query: str) -> list[dict[str, str | None]]:
        query = query.strip()
        if not query:
            return []
        return await self.client.search_ticketing_customers(query)

    async def get(self, customer_id: str | int) -> dict[str, Any]:
        return await self.client.get_ticketing_customer(customer_id)
