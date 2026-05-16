from __future__ import annotations

import uuid

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import CesarSmartApiClient
from .const import (
    CONF_DEVICE_ID,
    CONF_ENABLE_WEBSOCKET,
    CONF_LOCATION_INTERVAL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    CONF_USERNAME,
    CONF_VEHICLE_NAME,
    CONF_VIN,
    DEFAULT_ENABLE_WEBSOCKET,
    DEFAULT_LOCATION_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_LOCATION_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class CesarSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._api: CesarSmartApiClient | None = None
        self._auth_data: dict | None = None
        self._vehicles: list[dict] | None = None
        self._device_id: str | None = None
        self._user_input: dict | None = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            device_id = str(uuid.uuid4())
            api = CesarSmartApiClient(self.hass, device_id)
            try:
                auth_data = await api.async_login(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                vehicles = await api.async_get_security_objects(auth_data["access_token"])
            except Exception:
                errors["base"] = "auth"
            else:
                self._api = api
                self._auth_data = auth_data
                self._vehicles = vehicles
                self._device_id = device_id
                self._user_input = user_input
                if len(vehicles) == 1:
                    return self._create_entry(vehicles[0], self._user_input)
                return await self.async_step_select_vehicle(None)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_select_vehicle(self, user_input=None):
        if user_input is None:
            options = {}
            for i, v in enumerate(self._vehicles):
                brand = v.get("brandName", "")
                model = v.get("modelName", "")
                client = v.get("clientName", "")
                label = f"{brand} {model} - {client}"
                options[str(i)] = label
            return self.async_show_form(
                step_id="select_vehicle",
                data_schema=vol.Schema({
                    vol.Required("vehicle"): vol.In(options),
                }),
            )
        index = int(user_input["vehicle"])
        return self._create_entry(self._vehicles[index], self._user_input)

    def _create_entry(self, vehicle: dict, user_input: dict) -> dict:
        vin = vehicle.get("vin", "")
        unit_id = vehicle["units"][0]["unitId"]
        brand = vehicle.get("brandName", "")
        model = vehicle.get("modelName", "")
        client = vehicle.get("clientName", "")
        name = f"{brand} {model}" if brand else client

        data = {
            CONF_USERNAME: user_input[CONF_USERNAME],
            CONF_PASSWORD: user_input[CONF_PASSWORD],
            CONF_DEVICE_ID: self._device_id,
            CONF_VIN: vin,
            CONF_UNIT_ID: unit_id,
            CONF_VEHICLE_NAME: name,
            CONF_ENABLE_WEBSOCKET: DEFAULT_ENABLE_WEBSOCKET,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_LOCATION_INTERVAL: DEFAULT_LOCATION_INTERVAL,
        }
        if self._auth_data and "refresh_token" in self._auth_data:
            data["refresh_token"] = self._auth_data["refresh_token"]
        return self.async_create_entry(title=name, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CesarSmartOptionsFlow(config_entry)


class CesarSmartOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_ENABLE_WEBSOCKET,
                    default=self._config_entry.options.get(
                        CONF_ENABLE_WEBSOCKET,
                        DEFAULT_ENABLE_WEBSOCKET,
                    ),
                ): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self._config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                vol.Optional(
                    CONF_LOCATION_INTERVAL,
                    default=self._config_entry.options.get(
                        CONF_LOCATION_INTERVAL,
                        DEFAULT_LOCATION_INTERVAL,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_LOCATION_INTERVAL)),
            }),
        )
