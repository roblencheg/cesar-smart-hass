from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN

_REDACT_EXACT_LOWER = {
    "username",
    "password",
    "access_token",
    "refresh_token",
    "client_secret",
    "vin",
    "unitid",
    "unit_id",
    "device_id",
    "address",
}

_REDACT_PREFIX = {
    "ble_local_address",
    "ble_number",
    "rem_start_phone",
    "sim",
    "phone",
}

_REDACT_SUFFIX = {"latitude", "longitude", "course"}


def _should_redact(key: str) -> bool:
    kl = key.lower()
    if kl in _REDACT_EXACT_LOWER:
        return True
    for prefix in _REDACT_PREFIX:
        if kl.startswith(prefix):
            return True
    for suffix in _REDACT_SUFFIX:
        if kl.endswith(suffix):
            return True
    return False


def _redact(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _redact(v) if not _should_redact(k) else "**REDACTED**" for k, v in data.items()}
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
