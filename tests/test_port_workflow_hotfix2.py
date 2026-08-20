from app.routers.porting import _portability_summary, _validate_btn_workflow


def test_nested_earliest_estimate_is_attached_to_single_carrier_group():
    response = {
        "portablePhoneNumbers": [{
            "phoneNumbers": ["+18038542105"],
            "losingCarrier": {"name": "Frontier Rochester", "spid": "0121"},
            "portType": "NSR/1",
        }],
        "portabilityDetails": {"earliestEstimate": "2026-08-03T16:00:00-04:00"},
    }
    summary = _portability_summary(response)
    assert summary["groups"][0]["earliest_estimate_form"] == "2026-08-03T16:00"
    assert "Aug 3, 2026" in summary["groups"][0]["earliest_estimate"]


def test_partial_port_requires_replacement_btn_when_btn_is_porting():
    values = {
        "phoneNumbers": "8038542105 8038540398",
        "billingTelephoneNumber": "8038542105",
        "portingAllNumbers": False,
        "newBillingTelephoneNumber": "",
    }
    assert _validate_btn_workflow(values) is not None
    values["newBillingTelephoneNumber"] = "8035550000"
    assert _validate_btn_workflow(values) is None


def test_full_port_does_not_require_replacement_btn():
    values = {
        "phoneNumbers": "8038542105 8038540398",
        "billingTelephoneNumber": "8038542105",
        "portingAllNumbers": True,
        "newBillingTelephoneNumber": "",
    }
    assert _validate_btn_workflow(values) is None
