from app.routers.porting import _build_requested_foc, _port_profile


def test_manual_nsr_uses_date_only():
    value, triggered = _build_requested_foc("2026-08-04", "10:30", "NSR/1", "GEOGRAPHIC")
    assert value == "2026-08-04"
    assert triggered is None


def test_manual_oneport_uses_date_only():
    value, triggered = _build_requested_foc("2026-08-04", "09:00", "MANUAL", "GEOGRAPHIC")
    assert value == "2026-08-04"
    assert triggered is None


def test_automated_wireline_nonstandard_time_sets_triggered():
    value, triggered = _build_requested_foc("2026-08-04", "10:30", "AUTOMATED", "GEOGRAPHIC")
    assert value == "2026-08-04T10:30:00-0400"
    assert triggered is True


def test_automated_wireline_standard_time_omits_triggered():
    value, triggered = _build_requested_foc("2026-12-04", "11:30", "AUTOMATED", "GEOGRAPHIC")
    assert value == "2026-12-04T11:30:00-0500"
    assert triggered is False


def test_automated_wireless_omits_triggered():
    value, triggered = _build_requested_foc("2026-08-04", "10:30", "AUTOMATED", "WIRELESS")
    assert value == "2026-08-04T10:30:00-0400"
    assert triggered is None


def test_port_profiles():
    assert _port_profile("NSR/1")["kind"] == "manual"
    assert _port_profile("AUTOMATED", "WIRELESS")["kind"] == "automated_wireless"
    assert _port_profile("AUTOMATED", "GEOGRAPHIC")["kind"] == "automated_wireline"
