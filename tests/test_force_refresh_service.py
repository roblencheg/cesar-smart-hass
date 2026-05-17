from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import ServiceCall

from custom_components.cesar_smart import _handle_force_refresh
from custom_components.cesar_smart.const import DOMAIN


@pytest.mark.asyncio
async def test_force_refresh_all():
    coordinator = Mock()
    coordinator.async_request_refresh = AsyncMock()
    hass = Mock()
    hass.data = {DOMAIN: {"entry1": coordinator}}

    call = ServiceCall(DOMAIN, "force_refresh", {})
    await _handle_force_refresh(hass, call)
    coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_force_refresh_specific_entry():
    coord1 = Mock()
    coord1.async_request_refresh = AsyncMock()
    coord2 = Mock()
    coord2.async_request_refresh = AsyncMock()
    hass = Mock()
    hass.data = {DOMAIN: {"entry1": coord1, "entry2": coord2}}

    call = ServiceCall(DOMAIN, "force_refresh", {"entry_id": "entry1"})
    await _handle_force_refresh(hass, call)
    coord1.async_request_refresh.assert_awaited_once()
    coord2.async_request_refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_force_refresh_with_full_info():
    coordinator = Mock()
    coordinator.async_request_refresh = AsyncMock()
    hass = Mock()
    hass.data = {DOMAIN: {"entry1": coordinator}}

    call = ServiceCall(DOMAIN, "force_refresh", {"include_full_info": True})
    await _handle_force_refresh(hass, call)
    assert coordinator._full_info_last_update is None
    assert coordinator._location_last_update is None


@pytest.mark.asyncio
async def test_force_refresh_no_coordinators():
    hass = Mock()
    hass.data = {}
    call = ServiceCall(DOMAIN, "force_refresh", {})
    await _handle_force_refresh(hass, call)
