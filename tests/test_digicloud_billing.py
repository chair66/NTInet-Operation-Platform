import asyncio

from app.services.digicloud_platypus_billing import provision_residential_billing


class FakePlatypus:
    def __init__(self):
        self.add_rate_calls = []
        self.add_service_calls = []
        self.deleted_services = []

    async def get_rates(self, customer_id):
        return [{"rgid": "249", "crid": "13078"}]

    async def list_services2(self, customer_id, *, crid):
        return []

    async def list_service_tree(self, customer_id):
        return [{"rs_cr_id": "13078", "rs_svc_id": "300", "rs_path": "Digital Phone"}]

    async def get_service_info(self, service_id, *, rgid, crid):
        assert service_id == "300"
        assert (rgid, crid) == (0, "13078")
        return [
            {"datacol": "phone_number", "datahdr": "Phone Number", "readonly": "N", "reqd": "Y"},
            {"datacol": "mac_address", "datahdr": "MAC Address", "readonly": "N", "reqd": "Y"},
        ]

    async def add_rate(self, customer_id, rate_group_id, *, frequency, quantity):
        self.add_rate_calls.append((customer_id, rate_group_id))
        return "unexpected-new-crid"

    async def add_service(self, customer_id, *, service_type_id, crid, custom_fields):
        self.add_service_calls.append((customer_id, service_type_id, crid, custom_fields))
        return "service-data-1"

    async def delete_service(self, customer_id, *, service_type_id, data_id):
        self.deleted_services.append((customer_id, service_type_id, data_id))


def test_retry_reuses_incomplete_crid_and_discovers_digital_phone():
    client = FakePlatypus()
    result = asyncio.run(provision_residential_billing(
        client,
        customer_id="5001",
        rate_group_id="249",
        phone_number="8035551212",
        mac_address="",
        voicemail_pin="1234",
        voicemail_enabled=True,
        voicemail_email_enabled=False,
        email_address="customer@example.invalid",
        domain="ntinet.com",
    ))

    assert client.add_rate_calls == []
    assert result["crid"] == "13078"
    assert result["service_type_id"] == "300"
    assert result["reused_rate"] is True
    assert client.add_service_calls[0][1:3] == ("300", "13078")
