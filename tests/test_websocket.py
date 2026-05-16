from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.cesar_smart.websocket import (
    CesarSmartWebSocket,
    _normalize_ws_location,
)


@pytest.mark.asyncio
async def test_ws_event_status_changed():
    coordinator = Mock()
    coordinator.async_update_ws_statuses = AsyncMock()
    ws = CesarSmartWebSocket(Mock(), "token", "dev", coordinator)
    payload = {"PUSH_TYPE": "STATUS_CHANGED"}
    await ws._handle_event(payload)
    coordinator.async_update_ws_statuses.assert_awaited_once()


@pytest.mark.asyncio
async def test_ws_event_location_changed():
    coordinator = Mock()
    coordinator.async_update_ws_location = AsyncMock()
    ws = CesarSmartWebSocket(Mock(), "token", "dev", coordinator)
    payload = {
        "PUSH_TYPE": "LOCATION_CHANGED",
        "LATITUDE": 55.7558,
        "LONGITUDE": 37.6173,
        "COURSE": 90.0,
        "SPEED": 45.0,
        "DATE_MILLI": 1778919248000,
    }
    await ws._handle_event(payload)
    coordinator.async_update_ws_location.assert_awaited_once()
    loc = coordinator.async_update_ws_location.call_args[0][0]
    assert loc["latitude"] == 55.7558
    assert loc["longitude"] == 37.6173
    assert loc["course"] == 90.0
    assert loc["speedKm"] == 45.0
    assert loc["date"] == 1778919248000


@pytest.mark.asyncio
async def test_ws_event_command_status_ignored():
    coordinator = Mock()
    coordinator.async_update_ws_statuses = AsyncMock()
    coordinator.async_update_ws_location = AsyncMock()
    ws = CesarSmartWebSocket(Mock(), "token", "dev", coordinator)
    payload = {"PUSH_TYPE": "COMMAND_STATUS_CHANGED"}
    await ws._handle_event(payload)
    coordinator.async_update_ws_statuses.assert_not_awaited()
    coordinator.async_update_ws_location.assert_not_awaited()


@pytest.mark.asyncio
async def test_ws_event_unknown_ignored():
    coordinator = Mock()
    coordinator.async_update_ws_statuses = AsyncMock()
    ws = CesarSmartWebSocket(Mock(), "token", "dev", coordinator)
    payload = {"PUSH_TYPE": "UNKNOWN_TYPE"}
    await ws._handle_event(payload)
    coordinator.async_update_ws_statuses.assert_not_awaited()


@pytest.mark.asyncio
async def test_ws_event_no_push_type():
    coordinator = Mock()
    coordinator.async_update_ws_statuses = AsyncMock()
    ws = CesarSmartWebSocket(Mock(), "token", "dev", coordinator)
    payload = {"type": "STATUS_CHANGED"}
    await ws._handle_event(payload)
    coordinator.async_update_ws_statuses.assert_not_awaited()


def test_normalize_ws_location_uppercase():
    raw = {
        "LATITUDE": 55.0,
        "LONGITUDE": 37.0,
        "COURSE": 180.0,
        "SPEED": 60.0,
        "DATE_MILLI": 1000,
        "UNIT_ID": "u1",
    }
    n = _normalize_ws_location(raw)
    assert n["latitude"] == 55.0
    assert n["longitude"] == 37.0
    assert n["course"] == 180.0
    assert n["speedKm"] == 60.0
    assert n["date"] == 1000
    assert n["unitId"] == "u1"


def test_normalize_ws_location_other_cased():
    raw = {"Latitude": 1.0, "Longitude": 2.0, "SPEEDKM": 30.0}
    n = _normalize_ws_location(raw)
    assert n["latitude"] == 1.0
    assert n["longitude"] == 2.0
    assert n["speedKm"] == 30.0
