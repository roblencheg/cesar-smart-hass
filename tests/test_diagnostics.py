from __future__ import annotations

from custom_components.cesar_smart.diagnostics import _redact


def test_redact_sensitive_keys():
    data = {
        "username": "test_user",
        "password": "secret123",
        "access_token": "tok_123",
        "refresh_token": "ref_123",
        "vin": "XW7Bxxxxx",
        "unit_id": "unit_1",
        "latitude": 55.0,
        "longitude": 37.0,
        "safe_key": "keep_me",
    }
    redacted = _redact(data)
    assert redacted["username"] == "**REDACTED**"
    assert redacted["password"] == "**REDACTED**"
    assert redacted["access_token"] == "**REDACTED**"
    assert redacted["refresh_token"] == "**REDACTED**"
    assert redacted["vin"] == "**REDACTED**"
    assert redacted["unit_id"] == "**REDACTED**"
    assert redacted["latitude"] == "**REDACTED**"
    assert redacted["longitude"] == "**REDACTED**"
    assert redacted["safe_key"] == "keep_me"


def test_redact_rem_start_phone_sim():
    data = {
        "REM_START_PHONE_1": "+71234567890",
        "REM_START_PHONE_2": "+70987654321",
        "SIM1": "1234567890",
        "SIM2": "0987654321",
        "phone": "+70000000000",
        "ble_local_address": "AA:BB:CC:DD:EE:FF",
        "ble_number": "12345",
        "client_secret": "s3cr3t",
        "unitId": "u123",
        "device_id": "d456",
    }
    redacted = _redact(data)
    for key in data:
        assert redacted[key] == "**REDACTED**", f"Key {key} was not redacted"


def test_redact_uppercase_coordinates():
    data = {
        "LATITUDE": 55.0,
        "LONGITUDE": 37.0,
        "COURSE": 90.0,
        "ADDRESS": "Moscow",
    }
    redacted = _redact(data)
    assert redacted["LATITUDE"] == "**REDACTED**"
    assert redacted["LONGITUDE"] == "**REDACTED**"
    assert redacted["COURSE"] == "**REDACTED**"
    assert redacted["ADDRESS"] == "**REDACTED**"


def test_redact_address():
    data = {"address": "Some Street, 123"}
    redacted = _redact(data)
    assert redacted["address"] == "**REDACTED**"


def test_redact_safe_keys_preserved():
    data = {"engine_state": "STOPPED", "fuel_value": 31.0, "modelName": "H3"}
    redacted = _redact(data)
    assert redacted["engine_state"] == "STOPPED"
    assert redacted["fuel_value"] == 31.0
    assert redacted["modelName"] == "H3"
