from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.cesar_smart.const import DOMAIN
from custom_components.cesar_smart.coordinator import CesarSmartCoordinator


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


@pytest.fixture
def mock_hass():
    hass = Mock()
    hass.config_entries.async_update_entry = AsyncMock()
    return hass


@pytest.mark.asyncio
async def test_coordinator_initialization(mock_hass, mock_entry):
    with patch("aiohttp.ClientSession"):
        coordinator = CesarSmartCoordinator(mock_hass, mock_entry)
    assert coordinator.name == DOMAIN
    assert coordinator._vin == "XW7BXXXXX"
    assert coordinator._unit_id == "unit_123"


@pytest.mark.asyncio
async def test_coordinator_update(mock_hass, mock_entry):
    with patch("aiohttp.ClientSession"):
        coordinator = CesarSmartCoordinator(mock_hass, mock_entry)
    with patch.object(
        coordinator.api, "async_get_unit_statuses",
        AsyncMock(return_value={"ENGINE_STATE": "STOPPED"}),
    ), patch.object(
        coordinator.api, "async_get_location",
        AsyncMock(return_value={"latitude": 55.0, "longitude": 37.0}),
    ), patch.object(
        coordinator, "async_refresh_token_if_needed", AsyncMock()
    ):
        coordinator._access_token = "test_token"
        data = await coordinator._async_update_data()
        assert "statuses" in data
        assert data["statuses"]["ENGINE_STATE"] == "STOPPED"
        assert "location" in data


@pytest.mark.asyncio
async def test_coordinator_merge_full_info(mock_hass, mock_entry):
    with patch("aiohttp.ClientSession"):
        coordinator = CesarSmartCoordinator(mock_hass, mock_entry)
    stale = {"ENGINE_TEMP": 50, "FUEL_VALUE": 30}
    fresh_full = {"statuses": {"ENGINE_TEMP": 88, "SALON_TEMP": 22}}

    with patch.object(
        coordinator.api, "async_get_unit_statuses",
        AsyncMock(return_value=stale),
    ), patch.object(
        coordinator.api, "async_get_full_info",
        AsyncMock(return_value=fresh_full),
    ), patch.object(
        coordinator.api, "async_get_location",
        AsyncMock(return_value={"latitude": 55.0}),
    ), patch.object(
        coordinator, "async_refresh_token_if_needed", AsyncMock()
    ):
        coordinator._access_token = "test_token"
        coordinator._enable_full_info = True
        data = await coordinator._async_update_data()
        assert data["statuses"]["ENGINE_TEMP"] == 88
        assert data["statuses"]["FUEL_VALUE"] == 30
        assert data["statuses_raw"]["ENGINE_TEMP"] == 50
        assert data["full_info"] == fresh_full


@pytest.mark.asyncio
async def test_coordinator_ws_update_fetches_full_info(mock_hass, mock_entry):
    with patch("aiohttp.ClientSession"):
        coordinator = CesarSmartCoordinator(mock_hass, mock_entry)
    stale = {"ENGINE_TEMP": 50}
    fresh_full = {"statuses": {"ENGINE_TEMP": 88}}

    with patch.object(
        coordinator.api, "async_get_unit_statuses",
        AsyncMock(return_value=stale),
    ), patch.object(
        coordinator.api, "async_get_full_info",
        AsyncMock(return_value=fresh_full),
    ), patch.object(
        coordinator, "async_refresh_token_if_needed", AsyncMock()
    ):
        coordinator._access_token = "test_token"
        coordinator._enable_full_info = True
        await coordinator.async_update_ws_statuses()
        result = coordinator.data
        assert result is not None
        assert result["statuses"]["ENGINE_TEMP"] == 88
        assert result["statuses_raw"]["ENGINE_TEMP"] == 50
        assert result["full_info"] == fresh_full
