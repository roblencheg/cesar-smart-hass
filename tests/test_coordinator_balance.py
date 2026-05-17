from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

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
async def test_coordinator_balance_polling(mock_hass, mock_entry):
    with patch("aiohttp.ClientSession"):
        coordinator = CesarSmartCoordinator(mock_hass, mock_entry)
    balance_data = {"balance": 100, "currency": "RUB"}

    with patch.object(
        coordinator.api, "async_get_unit_statuses",
        AsyncMock(return_value={}),
    ), patch.object(
        coordinator.api, "async_get_full_info",
        AsyncMock(return_value=None),
    ), patch.object(
        coordinator.api, "async_get_location",
        AsyncMock(return_value=None),
    ), patch.object(
        coordinator.api, "async_get_balance",
        AsyncMock(return_value=balance_data),
    ), patch.object(
        coordinator, "async_refresh_token_if_needed", AsyncMock(),
    ):
        coordinator._access_token = "test_token"
        coordinator._enable_full_info = False
        data = await coordinator._async_update_data()
        assert "balance" in data
        assert data["balance"] == balance_data
