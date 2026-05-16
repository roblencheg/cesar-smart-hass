from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.cesar_smart.config_flow import CesarSmartConfigFlow
from custom_components.cesar_smart.const import DOMAIN

OAUTH_RESPONSE = {
    "access_token": "test_token",
    "refresh_token": "test_refresh",
    "expires_at": "2026-12-31T23:59:59+00:00",
}

SECURITY_OBJECTS = [
    {
        "vin": "XW7BXXXXX",
        "modelName": "H3",
        "brandName": "Haval",
        "clientName": "Test",
        "engineType": "benzine",
        "units": [{"unitId": "unit_123", "product": {"code": "C1"}}],
    }
]

MULTI_VEHICLES = [
    {
        "vin": "VIN001",
        "modelName": "H3",
        "brandName": "Haval",
        "clientName": "Car1",
        "engineType": "benzine",
        "units": [{"unitId": "unit_001", "product": {"code": "C1"}}],
    },
    {
        "vin": "VIN002",
        "modelName": "H9",
        "brandName": "Haval",
        "clientName": "Car2",
        "engineType": "benzine",
        "units": [{"unitId": "unit_002", "product": {"code": "C1"}}],
    },
]


@pytest.mark.asyncio
async def test_config_flow_user_form(hass: HomeAssistant):
    flow = CesarSmartConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_config_flow_success(hass: HomeAssistant):
    flow = CesarSmartConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.cesar_smart.config_flow.CesarSmartApiClient.async_login",
        AsyncMock(return_value=OAUTH_RESPONSE),
    ), patch(
        "custom_components.cesar_smart.config_flow.CesarSmartApiClient.async_get_security_objects",
        AsyncMock(return_value=SECURITY_OBJECTS),
    ):
        result = await flow.async_step_user(
            user_input={"username": "test@test.com", "password": "test123"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Haval H3"
        assert result["data"]["vin"] == "XW7BXXXXX"


@pytest.mark.asyncio
async def test_config_flow_multi_vehicle(hass: HomeAssistant):
    flow = CesarSmartConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.cesar_smart.config_flow.CesarSmartApiClient.async_login",
        AsyncMock(return_value=OAUTH_RESPONSE),
    ), patch(
        "custom_components.cesar_smart.config_flow.CesarSmartApiClient.async_get_security_objects",
        AsyncMock(return_value=MULTI_VEHICLES),
    ):
        result = await flow.async_step_user(
            user_input={"username": "user@test.com", "password": "pass"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "select_vehicle"

        result = await flow.async_step_select_vehicle({"vehicle": "1"})
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Haval H9"
        assert result["data"]["vin"] == "VIN002"
        assert result["data"]["username"] == "user@test.com"
        assert result["data"]["password"] == "pass"
        assert result["data"]["unit_id"] == "unit_002"


@pytest.mark.asyncio
async def test_config_flow_auth_failure(hass: HomeAssistant):
    flow = CesarSmartConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.cesar_smart.config_flow.CesarSmartApiClient.async_login",
        AsyncMock(side_effect=Exception("auth failed")),
    ):
        result = await flow.async_step_user(
            user_input={"username": "test@test.com", "password": "wrong"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"]["base"] == "auth"


@pytest.mark.asyncio
async def test_options_flow(hass: HomeAssistant):
    from tests.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test", "password": "test"},
        options={},
    )
    entry.add_to_hass(hass)
    flow = CesarSmartConfigFlow()
    flow.hass = hass
    options_flow = CesarSmartConfigFlow.async_get_options_flow(entry)
    options_flow.hass = hass
    result = await options_flow.async_step_init(user_input=None)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"
