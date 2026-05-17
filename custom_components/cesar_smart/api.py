from __future__ import annotations

import base64
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from .const import (
    BASE_API_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    OAUTH_API_URL,
    TOKEN_EXPIRY_BUFFER,
)

_LOGGER = logging.getLogger(__name__)

_REDACT_WORDS = {
    "access_token",
    "refresh_token",
    "password",
    "authorization",
    "bearer",
    "basic",
}


def _redact_sensitive(value: Any) -> Any:
    """Redact sensitive strings from debug logs."""
    if isinstance(value, str):
        lower = value.lower()
        if len(value) > 8 and any(w in lower for w in _REDACT_WORDS):
            return value[:4] + "**REDACTED**"
        return value
    return value


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
        basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("ascii")
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json;charset=UTF-8",
            "User-Agent": "CesarSmart/3.9 HomeAssistant",
        }
        async with self._s.post(
            OAUTH_API_URL.rstrip("/") + "/oauth/token",
            data=data,
            headers=headers,
        ) as resp:
            if resp.status == 401:
                _LOGGER.error(
                    "OAuth 401 Unauthorized. Check OAuth client headers and user credentials."
                )
                _LOGGER.debug("OAuth 401 body: %s", await resp.text())
                raise CesarSmartAuthError("OAuth failed: 401 Unauthorized")
            if resp.status != 200:
                _LOGGER.error("OAuth error %s", resp.status)
                _LOGGER.debug("OAuth error body: %s", await resp.text())
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
        start = time.monotonic()
        async with self._s.request(method, url, headers=headers, **kwargs) as resp:
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status == 401:
                raise CesarSmartAuthError("Token expired")
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("API error %s %s: %s", method, url, text)
                raise CesarSmartApiError(f"API error {resp.status}")
            result = await resp.json()
            _LOGGER.debug(
                "%s %s status=%s %sms keys=%s",
                method,
                path,
                resp.status,
                elapsed,
                list(result.keys()) if isinstance(result, dict) else type(result).__name__,
            )
            return result

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
        result = data.get("data", {})
        _LOGGER.debug("Statuses keys: %s", list(result.keys()))
        return result

    async def async_get_location(self, access_token: str, unit_id: str) -> dict | None:
        data = await self._request(
            "GET", f"/api/v2/location?unitId={unit_id}", access_token
        )
        return data.get("data")

    async def async_get_balance(self, access_token: str, vin: str, unit_id: str) -> Any:
        response = await self._request(
            "GET",
            f"/api/v2/security_objects/units/balance/?vin={vin}&unitId={unit_id}",
            access_token,
        )
        if response is None:
            return None
        if not isinstance(response, dict):
            return response
        _LOGGER.debug(
            "SIM balance raw response keys=%s",
            list(response.keys()),
        )
        data = response.get("data")
        if data is not None:
            _LOGGER.debug(
                "SIM balance data type=%s keys=%s",
                type(data).__name__,
                list(data.keys()) if isinstance(data, dict) else None,
            )
            return data
        _BALANCE_TOP_KEYS = {
            "balance", "value", "amount", "sum", "money",
            "accountBalance", "simBalance", "rest",
            "currency", "currencyCode",
        }
        if any(k in response for k in _BALANCE_TOP_KEYS):
            _LOGGER.debug("SIM balance using top-level response fallback")
            return response
        _LOGGER.debug("SIM balance response has no data field and no known balance keys")
        return response

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
