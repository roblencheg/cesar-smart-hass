from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from .const import (
    BASE_API_URL,
    OAUTH_API_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    TOKEN_EXPIRY_BUFFER,
)

_LOGGER = logging.getLogger(__name__)


class CesarSmartAuthError(Exception):
    pass


class CesarSmartApiError(Exception):
    pass


class CesarSmartApiClient:
    def __init__(self, hass, device_id: str, session: aiohttp.ClientSession | None = None):
        self._hass = hass
        self._device_id = device_id
        self._session = session

    @property
    def _s(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def async_login(self, username: str, password: str) -> dict:
        return await self._async_token_request({
            "grant_type": "password",
            "device_id": self._device_id,
            "scope": "all",
            "username": username,
            "password": password,
        })

    async def async_refresh_token(self, refresh_token: str) -> dict:
        return await self._async_token_request({
            "grant_type": "refresh_token",
            "device_id": self._device_id,
            "refresh_token": refresh_token,
        })

    async def _async_token_request(self, data: dict) -> dict:
        auth = aiohttp.BasicAuth(CLIENT_ID, CLIENT_SECRET)
        async with self._s.post(
            OAUTH_API_URL + "oauth/token",
            data=data,
            auth=auth,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("OAuth error %s: %s", resp.status, text)
                raise CesarSmartAuthError(f"OAuth failed: {resp.status}")
            result = await resp.json()
            result["expires_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=result.get("expires_in", 119))
            ).isoformat()
            return result

    def is_token_expired(self, expires_at: str) -> bool:
        if not expires_at:
            return True
        expiry = datetime.fromisoformat(expires_at)
        return datetime.now(timezone.utc) >= (expiry - timedelta(seconds=TOKEN_EXPIRY_BUFFER))

    async def _request(self, method: str, path: str, access_token: str, **kwargs) -> dict:
        url = BASE_API_URL.rstrip("/") + "/" + path.lstrip("/")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "X-CS-TW-APP-TYPE": "cesarSmart",
            "X-CS-TW-APP-VERSION": "3.9 (444)",
            "X-CS-TW-PLATFORM": "ANDROID",
        }
        headers.update(kwargs.pop("headers", {}))
        async with self._s.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:
                raise CesarSmartAuthError("Token expired")
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("API error %s %s: %s", method, url, text)
                raise CesarSmartApiError(f"API error {resp.status}")
            return await resp.json()

    async def async_get_security_objects(self, access_token: str) -> list[dict]:
        data = await self._request("GET", "/api/v2/security_objects/", access_token)
        return data.get("data", [])

    async def async_get_full_info(self, access_token: str, vin: str) -> dict:
        return await self._request(
            "GET", f"/api/v2/security_objects/full?vin={vin}", access_token
        )

    async def async_get_unit_statuses(self, access_token: str, unit_id: str) -> dict:
        data = await self._request(
            "GET", f"/api/v2/security_objects/units/statuses?unitId={unit_id}", access_token
        )
        return data.get("data", {})

    async def async_get_location(self, access_token: str, unit_id: str) -> dict | None:
        data = await self._request(
            "GET", f"/api/v2/location?unitId={unit_id}", access_token
        )
        return data.get("data")

    async def async_get_balance(self, access_token: str, vin: str, unit_id: str) -> dict | None:
        data = await self._request(
            "GET",
            f"/api/v2/security_objects/units/balance/?vin={vin}&unitId={unit_id}",
            access_token,
        )
        return data.get("data")

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
