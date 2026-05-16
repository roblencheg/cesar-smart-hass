from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web

from custom_components.cesar_smart.api import CesarSmartApiClient, CesarSmartAuthError
from custom_components.cesar_smart.const import CLIENT_ID

OAUTH_RESPONSE = {
    "access_token": "test_access_token",
    "refresh_token": "test_refresh_token",
    "token_type": "bearer",
    "expires_in": 119,
    "scope": "all",
}

STATUSES_RESPONSE = {
    "code": "OK",
    "data": {
        "ENGINE_STATE": "STOPPED",
        "MODE": "GUARD_MODE_ON",
        "FUEL_VALUE": 31.0,
        "MILEAGE_KM": 2915,
        "VEHICLE_CHARGE_VOLT": 12.7,
        "ENGINE_TEMP": 14,
        "SALON_TEMP": 30,
        "OUTDOOR_TEMP": 12,
    },
    "error": None,
}

LOCATION_RESPONSE = {
    "code": "OK",
    "data": {
        "date": 1778919248000,
        "latitude": 55.0,
        "longitude": 37.0,
        "speedKm": 0.0,
        "course": 0.0,
        "unitId": None,
    },
    "error": None,
}

SECURITY_OBJECTS_RESPONSE = {
    "code": "OK",
    "data": [
        {
            "vin": "XW7BXXXXX",
            "modelName": "H3",
            "brandName": "Haval",
            "clientName": "Test User",
            "engineType": "benzine",
            "units": [
                {
                    "unitId": "unit_123",
                    "unitClass": "GUARD",
                    "protocol": "CESAR33",
                    "statuses": {},
                    "product": {"code": "C1", "name": "C1"},
                }
            ],
        }
    ],
    "error": None,
}


def test_client_id():
    assert CLIENT_ID == "ma_cesar_key"


@pytest.fixture
def client():
    return CesarSmartApiClient(None, "test_device_id")


@pytest.mark.asyncio
async def test_login_success(client):
    with patch.object(client, "_async_token_request", AsyncMock(return_value=OAUTH_RESPONSE)):
        result = await client.async_login("user", "pass")
        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"


@pytest.mark.asyncio
async def test_login_failure(client):
    with patch.object(client, "_async_token_request", AsyncMock(side_effect=CesarSmartAuthError("fail"))):
        with pytest.raises(CesarSmartAuthError):
            await client.async_login("user", "pass")


@pytest.mark.asyncio
async def test_refresh_token(client):
    with patch.object(client, "_async_token_request", AsyncMock(return_value=OAUTH_RESPONSE)):
        result = await client.async_refresh_token("old_refresh")
        assert result["access_token"] == "test_access_token"


@pytest.mark.asyncio
async def test_get_security_objects(client):
    with patch.object(client, "_request", AsyncMock(return_value=SECURITY_OBJECTS_RESPONSE)):
        result = await client.async_get_security_objects("token")
        assert len(result) == 1
        assert result[0]["brandName"] == "Haval"


@pytest.mark.asyncio
async def test_get_statuses(client):
    with patch.object(client, "_request", AsyncMock(return_value=STATUSES_RESPONSE)):
        result = await client.async_get_unit_statuses("token", "unit_123")
        assert result["ENGINE_STATE"] == "STOPPED"
        assert result["MILEAGE_KM"] == 2915


@pytest.mark.asyncio
async def test_get_location(client):
    with patch.object(client, "_request", AsyncMock(return_value=LOCATION_RESPONSE)):
        result = await client.async_get_location("token", "unit_123")
        assert result["latitude"] == 55.0
        assert result["longitude"] == 37.0


@pytest.mark.asyncio
async def test_401_raises_auth_error(client):
    with patch.object(client, "_request", AsyncMock(side_effect=CesarSmartAuthError("Token expired"))):
        with pytest.raises(CesarSmartAuthError):
            await client.async_get_unit_statuses("bad_token", "unit_123")
