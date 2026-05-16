from __future__ import annotations

import logging
from datetime import timedelta, datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CesarSmartApiClient, CesarSmartAuthError
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DEVICE_ID,
    CONF_VIN,
    CONF_UNIT_ID,
    CONF_ENABLE_WEBSOCKET,
    CONF_SCAN_INTERVAL,
    CONF_LOCATION_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_LOCATION_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CesarSmartCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._entry = entry
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._vin = entry.data.get(CONF_VIN, "")
        self._unit_id = entry.data.get(CONF_UNIT_ID, "")
        self._username = entry.data[CONF_USERNAME]
        self._password = entry.data[CONF_PASSWORD]
        self._access_token: str | None = None
        self._refresh_token: str | None = entry.data.get("refresh_token")
        self._expires_at: str | None = entry.data.get("expires_at")
        self._ws_task = None

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        location_interval = entry.options.get(CONF_LOCATION_INTERVAL, entry.data.get(CONF_LOCATION_INTERVAL, DEFAULT_LOCATION_INTERVAL))

        self._location_interval = timedelta(seconds=location_interval)
        self._location_last_update: datetime | None = None
        self._location_data: dict | None = None
        self._balance_data: dict | None = None

        self.api = CesarSmartApiClient(hass, self._device_id)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_refresh_token_if_needed(self):
        if self._refresh_token and self._expires_at:
            if self.api.is_token_expired(self._expires_at):
                try:
                    auth = await self.api.async_refresh_token(self._refresh_token)
                    self._access_token = auth["access_token"]
                    self._refresh_token = auth.get("refresh_token", self._refresh_token)
                    self._expires_at = auth["expires_at"]
                    self._update_entry_tokens()
                except CesarSmartAuthError:
                    _LOGGER.warning("Token refresh failed, re-logging in")
                    await self._async_relogin()
        elif not self._access_token:
            await self._async_relogin()

    async def _async_relogin(self):
        auth = await self.api.async_login(self._username, self._password)
        self._access_token = auth["access_token"]
        self._refresh_token = auth.get("refresh_token")
        self._expires_at = auth["expires_at"]
        self._update_entry_tokens()

    def _update_entry_tokens(self):
        self.hass.config_entries.async_update_entry(
            self._entry,
            data={
                **self._entry.data,
                "refresh_token": self._refresh_token,
                "expires_at": self._expires_at,
            },
        )

    async def _async_update_data(self) -> dict:
        try:
            await self.async_refresh_token_if_needed()
            token = self._access_token

            data: dict = {}

            statuses = await self.api.async_get_unit_statuses(token, self._unit_id)
            data["statuses"] = statuses

            now = datetime.now(timezone.utc)
            if (
                self._location_last_update is None
                or (now - self._location_last_update) >= self._location_interval
            ):
                location = await self.api.async_get_location(token, self._unit_id)
                if location:
                    self._location_data = location
                    self._location_last_update = now
            data["location"] = self._location_data

            return data

        except CesarSmartAuthError:
            try:
                await self._async_relogin()
                token = self._access_token
                statuses = await self.api.async_get_unit_statuses(token, self._unit_id)
                data = {"statuses": statuses, "location": self._location_data}
                return data
            except Exception as err:
                raise UpdateFailed(f"Auth retry failed: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}") from err

    async def async_update_ws_statuses(self):
        try:
            await self.async_refresh_token_if_needed()
            statuses = await self.api.async_get_unit_statuses(self._access_token, self._unit_id)
            self.async_set_updated_data({**self.data, "statuses": statuses})
        except Exception as err:
            _LOGGER.warning("WS status update error: %s", err)

    async def async_update_ws_location(self, location_data: dict):
        self._location_data = location_data
        self._location_last_update = datetime.now(timezone.utc)
        self.async_set_updated_data({**self.data, "location": location_data})

    async def async_shutdown(self):
        if hasattr(self, "api") and self.api:
            await self.api.close()
