import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS
from .coordinator import CesarSmartCoordinator
from .data_extractors import (
    extract_balance_currency,
    extract_balance_updated_at,
    extract_balance_value,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

FORCE_REFRESH_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("include_full_info", default=True): cv.boolean,
    vol.Optional("include_balance", default=True): cv.boolean,
})

BALANCE_PROBE_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
})


async def _handle_balance_probe(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = call.data.get("entry_id")
    coordinators: dict[str, CesarSmartCoordinator] = hass.data.get(DOMAIN, {})
    if not coordinators:
        _LOGGER.warning("balance_probe: no coordinators found")
        return

    targets = {entry_id: coordinators[entry_id]} if entry_id else coordinators
    for eid, coordinator in targets.items():
        try:
            await coordinator.async_refresh_token_if_needed()
            token = coordinator._access_token
            response = await coordinator.api.async_get_balance(
                token, coordinator._vin, coordinator._unit_id,
            )
            _LOGGER.debug("=== balance_probe entry=%s ===", eid)
            _LOGGER.debug("response type=%s", type(response).__name__)
            if isinstance(response, dict):
                _LOGGER.debug("response keys=%s", list(response.keys()))
            value = extract_balance_value(response)
            currency = extract_balance_currency(response)
            updated = extract_balance_updated_at(response)
            _LOGGER.debug("extracted value=%s currency=%s updated_at=%s", value, currency, updated)
            coordinator._balance_raw_data = response
            coordinator._balance_data = response
            current = coordinator.data or {}
            coordinator.async_set_updated_data({
                **current,
                "balance": response,
                "balance_raw": response,
            })
        except Exception as err:
            _LOGGER.error("balance_probe entry=%s failed: %s", eid, err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def _handle_force_refresh(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = call.data.get("entry_id")
    include_full_info = call.data.get("include_full_info", True)
    include_balance = call.data.get("include_balance", True)

    coordinators: dict[str, CesarSmartCoordinator] = hass.data.get(DOMAIN, {})
    if not coordinators:
        return

    if entry_id:
        coordinator = coordinators.get(entry_id)
        if not coordinator:
            _LOGGER.warning("force_refresh requested unknown entry_id=%s", entry_id)
            return
        targets = {entry_id: coordinator}
    else:
        targets = coordinators
    for eid, coordinator in targets.items():
        if include_full_info:
            coordinator._full_info_last_update = None
            coordinator._location_last_update = None
        if include_balance:
            coordinator._balance_last_update = None
        await coordinator.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = CesarSmartCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_start_websocket()

    if not hass.services.has_service(DOMAIN, "force_refresh"):
        hass.services.async_register(
            DOMAIN,
            "force_refresh",
            _handle_force_refresh,
            schema=FORCE_REFRESH_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "balance_probe"):
        hass.services.async_register(
            DOMAIN,
            "balance_probe",
            _handle_balance_probe,
            schema=BALANCE_PROBE_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            await coordinator.async_shutdown()
    return unload_ok
