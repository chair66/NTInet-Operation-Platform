import asyncio

from app.services.platypus import PlatypusClient, PlatypusResponse


class RecordingPlatypus(PlatypusClient):
    def __init__(self):
        self.calls = []

    async def call(self, action, *, parameters=(), properties=()):
        self.calls.append((action, tuple(parameters), tuple(properties)))
        return PlatypusResponse(
            action=action,
            response_code="SUCCESS",
            response_text="The customer was successfully added.",
            is_success=True,
            records=[{"custid": "1531"}],
        )


def test_add_customer_uses_documented_addtoplat_shape_without_rates():
    client = RecordingPlatypus()
    result = asyncio.run(client.add_customer(
        name="Example Customer",
        phone="803-555-1212",
        username="billing@example.invalid",
        email="billing@example.invalid",
        address_line_1="100 Main Street",
        city="Orangeburg",
        state="sc",
        postal_code="29115",
        temporary_password="one-time-secret",
    ))

    action, parameters, properties = client.calls[0]
    props = dict(properties)
    assert action == "AddToPlat"
    assert dict(parameters) == {"activeconn": "false", "datatype": "XML"}
    assert props["billingmeth"] == "check"
    assert props["phone"] == "8035551212"
    assert props["selectrate"] == "-1"
    assert props["password"] == "one-time-secret"
    assert result["customer_id"] == "1531"


def test_add_customer_requires_complete_identity_before_provider_call():
    client = RecordingPlatypus()
    try:
        asyncio.run(client.add_customer(
            name="",
            phone="8035551212",
            username="billing@example.invalid",
            address_line_1="100 Main Street",
            city="Orangeburg",
            state="SC",
            postal_code="29115",
        ))
    except ValueError as exc:
        assert "Customer name" in str(exc)
    else:
        raise AssertionError("Incomplete customer was sent to Platypus")
    assert client.calls == []
