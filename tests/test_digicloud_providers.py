from types import SimpleNamespace

from app.providers.netsapiens.phonenumbers import NetSapiensPhoneNumbers
from app.routers.digicloud import _resolve_billing_target
from app.services.digicloud_platypus_billing import normalize_mac


class RecordingClient:
    def __init__(self, result=None):
        self.result = result if result is not None else {"ok": True}
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return self.result


def test_did_assignment_uses_country_code_route_and_ten_digit_subscriber():
    client = RecordingClient()
    provider = NetSapiensPhoneNumbers(client)

    provider.update_in_domain(
        "ntinet.com",
        "803-555-1212",
        destination_user="8035551212",
        description="Test Subscriber",
        treatment="user",
        enabled=True,
    )

    method, path, kwargs = client.calls[0]
    assert method == "PUT"
    assert path == "/domains/ntinet.com/phonenumbers/18035551212"
    assert kwargs["json"]["dial-rule-translation-destination-user"] == "8035551212"
    assert kwargs["json"]["enabled"] == "yes"


def test_manual_and_no_device_billing_allow_empty_mac():
    assert normalize_mac("", required=False) == ""


def test_inventory_hardware_requires_valid_mac():
    try:
        normalize_mac("not-a-mac")
    except ValueError as exc:
        assert "12 hexadecimal" in str(exc)
    else:
        raise AssertionError("Invalid inventory MAC was accepted")

    assert normalize_mac("aa:bb:cc:dd:ee:ff") == "AABBCCDDEEFF"


def test_wholesale_posted_billing_customer_override_is_ignored():
    settings = SimpleNamespace(
        billing_model="wholesale",
        platypus_parent_customer_id="trusted-parent-42",
        wholesale_rate_group_ids='["700", "701"]',
    )

    customer_id, rate_group_id, allowed = _resolve_billing_target(
        settings,
        posted_customer_id="attacker-selected-customer",
        posted_rate_group_id="701",
    )

    assert customer_id == "trusted-parent-42"
    assert rate_group_id == "701"
    assert allowed == {"700", "701"}
