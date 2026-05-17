from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.core import ServiceCall

from custom_components.cesar_smart import _handle_balance_probe
from custom_components.cesar_smart.const import DOMAIN


@pytest.mark.asyncio
async def test_balance_probe_registered():
    hass = Mock()
    coord = Mock()
    coord.async_refresh_token_if_needed = AsyncMock()
    coord._access_token = "test_token"
    coord._vin = "XW7BXXXXX"
    coord._unit_id = "unit_123"
    coord.api.async_get_balance = AsyncMock(
        return_value={"balance": 100, "currency": "RUB"},
    )
    coord.async_set_updated_data = Mock()
    coord.data = {}
    hass.data = {DOMAIN: {"entry1": coord}}

    call = ServiceCall(DOMAIN, "balance_probe", {})
    await _handle_balance_probe(hass, call)

    coord.async_refresh_token_if_needed.assert_awaited_once()
    coord.api.async_get_balance.assert_awaited_once_with(
        "test_token", "XW7BXXXXX", "unit_123",
    )
    coord.async_set_updated_data.assert_called_once()
    assert coord._balance_data == {"balance": 100, "currency": "RUB"}
    assert coord._balance_raw_data == {"balance": 100, "currency": "RUB"}


@pytest.mark.asyncio
async def test_balance_probe_no_coordinators():
    hass = Mock()
    hass.data = {}
    call = ServiceCall(DOMAIN, "balance_probe", {})
    await _handle_balance_probe(hass, call)


@pytest.mark.asyncio
async def test_balance_probe_specific_entry():
    coord1 = Mock()
    coord1.async_refresh_token_if_needed = AsyncMock()
    coord1.api.async_get_balance = AsyncMock(return_value={"balance": 100})
    coord1.async_set_updated_data = Mock()
    coord1.data = {}
    coord1._access_token = "t1"
    coord1._vin = "v1"
    coord1._unit_id = "u1"

    coord2 = Mock()
    coord2.async_refresh_token_if_needed = AsyncMock()
    coord2.api.async_get_balance = AsyncMock(return_value={"balance": 200})
    coord2.async_set_updated_data = Mock()
    coord2.data = {}
    coord2._access_token = "t2"
    coord2._vin = "v2"
    coord2._unit_id = "u2"

    hass = Mock()
    hass.data = {DOMAIN: {"entry1": coord1, "entry2": coord2}}

    call = ServiceCall(DOMAIN, "balance_probe", {"entry_id": "entry1"})
    await _handle_balance_probe(hass, call)

    coord1.api.async_get_balance.assert_awaited_once()
    coord2.api.async_get_balance.assert_not_awaited()
