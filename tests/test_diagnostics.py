from __future__ import annotations

from custom_components.cesar_smart.diagnostics import _redact


async def test_redact_sensitive_keys():
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
