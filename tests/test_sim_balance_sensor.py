from __future__ import annotations

from unittest.mock import Mock

import pytest

from custom_components.cesar_smart.sensor import CesarSimBalanceSensor


@pytest.fixture
def mock_entry():
    entry = Mock()
    entry.data = {
        "username": "test",
        "password": "test",
        "device_id": "test_device",
        "vin": "XW7BXXXXX",
        "unit_id": "unit_123",
        "vehicle_name": "Haval H3",
        "refresh_token": "test_refresh",
        "expires_at": "2099-01-01T00:00:00+00:00",
    }
    entry.options = {}
    entry.entry_id = "test_entry"
    return entry


def _make_coordinator(data: dict | None = None, debug: bool = False):
    coord = Mock()
    coord.data = data or {}
    coord.last_update = "2025-01-01T00:00:00+00:00"
    coord._debug_attributes = debug
    return coord


def test_native_value(mock_entry):
    coordinator = _make_coordinator({"balance": {"balance": 100, "currency": "RUB"}})
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    assert sensor.native_value == 100.0


def test_native_value_none(mock_entry):
    coordinator = _make_coordinator({})
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    assert sensor.native_value is None


def test_native_value_fallback_to_raw(mock_entry):
    coordinator = _make_coordinator({
        "balance": None,
        "balance_raw": {"result": {"accountBalance": "50"}},
    })
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    assert sensor.native_value == 50.0


def test_extra_state_attributes_currency(mock_entry):
    coordinator = _make_coordinator({"balance": {"balance": 100, "currency": "RUB"}})
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["currency"] == "RUB"
    assert attrs["has_balance_data"] is True


def test_extra_state_attributes_updated_at(mock_entry):
    coordinator = _make_coordinator({
        "balance": {"balance": 100, "updatedAt": "2026-05-17T10:00:00Z"},
    })
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["updated_at"] == "2026-05-17T10:00:00Z"


def test_extra_state_attributes_no_balance(mock_entry):
    coordinator = _make_coordinator({})
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["has_balance_data"] is False


def test_extra_state_attributes_no_balance_but_raw(mock_entry):
    coordinator = _make_coordinator({
        "balance": None,
        "balance_raw": {"result": {"accountBalance": "50"}},
    })
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["has_balance_data"] is False
    assert attrs["parsed_value"] == 50.0


def test_debug_attributes_raw(mock_entry):
    balance_data = {"balance": 100, "currency": "RUB"}
    balance_raw = {"full_response": {"balance": 100}}
    coordinator = _make_coordinator(
        {"balance": balance_data, "balance_raw": balance_raw}, debug=True,
    )
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["raw_balance"] == balance_data
    assert attrs["raw_balance_response"] == balance_raw


def test_icon_is_sim(mock_entry):
    coordinator = _make_coordinator({})
    sensor = CesarSimBalanceSensor(coordinator, mock_entry)
    assert sensor.icon == "mdi:sim"
