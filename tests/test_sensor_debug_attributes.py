from __future__ import annotations

from unittest.mock import Mock

import pytest

from custom_components.cesar_smart.sensor import CesarStatusSensor


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


def _make_coordinator(data: dict | None = None, debug: bool = True):
    coord = Mock()
    coord.data = data or {}
    coord.last_update = "2025-01-01T00:00:00+00:00"
    coord._debug_attributes = debug
    return coord


def test_debug_full_info_value_from_data_statuses(mock_entry):
    coordinator = _make_coordinator({
        "statuses": {"ENGINE_TEMP": 88},
        "statuses_raw": {"ENGINE_TEMP": 50},
        "full_info": {"data": {"statuses": {"ENGINE_TEMP": 88}}},
    })
    sensor = CesarStatusSensor(coordinator, mock_entry, "ENGINE_TEMP", {
        "name": "Engine Temperature",
        "icon": "mdi:thermometer",
        "unit": "\u00b0C",
        "device_class": "temperature",
        "state_class": "measurement",
    })
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["full_info_value"] == 88


def test_debug_full_info_value_from_top_level_statuses(mock_entry):
    coordinator = _make_coordinator({
        "statuses": {"ENGINE_TEMP": 90},
        "statuses_raw": {"ENGINE_TEMP": 50},
        "full_info": {"statuses": {"ENGINE_TEMP": 90}},
    })
    sensor = CesarStatusSensor(coordinator, mock_entry, "ENGINE_TEMP", {
        "name": "Engine Temperature",
        "icon": "mdi:thermometer",
        "unit": "\u00b0C",
        "device_class": "temperature",
        "state_class": "measurement",
    })
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["full_info_value"] == 90


def test_debug_full_info_value_nested_in_unit_statuses(mock_entry):
    coordinator = _make_coordinator({
        "statuses": {"ENGINE_TEMP": 85},
        "statuses_raw": {"ENGINE_TEMP": 70},
        "full_info": {"unit": {"statuses": {"ENGINE_TEMP": 85}}},
    })
    sensor = CesarStatusSensor(coordinator, mock_entry, "ENGINE_TEMP", {
        "name": "Engine Temperature",
        "icon": "mdi:thermometer",
        "unit": "\u00b0C",
        "device_class": "temperature",
        "state_class": "measurement",
    })
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["full_info_value"] == 85


def test_debug_full_info_value_absent(mock_entry):
    coordinator = _make_coordinator({
        "statuses": {"ENGINE_TEMP": 88},
        "statuses_raw": {"ENGINE_TEMP": 88},
        "full_info": None,
    })
    sensor = CesarStatusSensor(coordinator, mock_entry, "ENGINE_TEMP", {
        "name": "Engine Temperature",
        "icon": "mdi:thermometer",
        "unit": "\u00b0C",
        "device_class": "temperature",
        "state_class": "measurement",
    })
    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["full_info_value"] is None


def test_debug_disabled_returns_none(mock_entry):
    coordinator = _make_coordinator({
        "statuses": {"ENGINE_TEMP": 88},
        "statuses_raw": {"ENGINE_TEMP": 88},
        "full_info": None,
    }, debug=False)
    sensor = CesarStatusSensor(coordinator, mock_entry, "ENGINE_TEMP", {
        "name": "Engine Temperature",
        "icon": "mdi:thermometer",
        "unit": "\u00b0C",
        "device_class": "temperature",
        "state_class": "measurement",
    })
    assert sensor.extra_state_attributes is None
