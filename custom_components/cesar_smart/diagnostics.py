from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN

REDACT_KEYS = {
    "username",
    "password",
    "access_token",
    "refresh_token",
    "client_secret",
    "vin",
    "unitId",
    "unit_id",
    "device_id",
    "BLE_LOCAL_ADDRESS",
    "BLE_NUMBER",
    "REM_START_PHONE_",
    "SIM1",
    "SIM2",
    "latitude",
    "longitude",
    "course",
}


def _redact(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _redact(v) if k not in REDACT_KEYS else "**REDACTED**" for k, v in data.items()}
    if isinstance(data, list):
        return [_redact(item) for item in data]
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    data = {
        "entry_data": _redact(dict(entry.data)),
        "entry_options": dict(entry.options),
    }
    if coordinator:
        data["coordinator_data"] = _redact(coordinator.data)
    return data


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict:
    return await async_get_config_entry_diagnostics(hass, entry)
