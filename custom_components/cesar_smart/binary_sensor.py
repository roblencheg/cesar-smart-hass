from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BINARY_SENSOR_MAP,
    DOMAIN,
    MANUFACTURER,
    STOPPED_STATES,
    device_id_from_vin_unit,
)
from .coordinator import CesarSmartCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator: CesarSmartCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    for source_key, config in BINARY_SENSOR_MAP.items():
        entities.append(CesarBinarySensor(coordinator, entry, source_key, config))

    entities.append(CesarEngineRunningSensor(coordinator, entry))
    entities.append(CesarRemoteStartSensor(coordinator, entry))

    async_add_entities(entities)


class CesarBaseEntity(CoordinatorEntity):
    def __init__(
        self,
        coordinator: CesarSmartCoordinator,
        entry: ConfigEntry,
        name: str,
        key: str,
    ):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        dev_id = device_id_from_vin_unit(
            entry.data.get("vin", ""), entry.data.get("unit_id", "")
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, dev_id)},
            "name": entry.data.get("vehicle_name", "Cesar Smart Vehicle"),
            "manufacturer": MANUFACTURER,
            "model": "",
        }


class CesarBinarySensor(CesarBaseEntity, BinarySensorEntity):
    def __init__(
        self,
        coordinator: CesarSmartCoordinator,
        entry: ConfigEntry,
        source_key: str,
        config: dict,
    ):
        super().__init__(coordinator, entry, config["name"], source_key)
        self._source_key = source_key
        self._on_value = config["on_value"]
        self._attr_device_class = config["device_class"]

    @property
    def is_on(self):
        statuses = self.coordinator.data.get("statuses", {})
        return statuses.get(self._source_key) == self._on_value


class CesarEngineRunningSensor(CesarBaseEntity, BinarySensorEntity):
    def __init__(self, coordinator: CesarSmartCoordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry, "Engine Running", "engine_running")
        self._attr_device_class = "power"

    @property
    def is_on(self):
        statuses = self.coordinator.data.get("statuses", {})
        return statuses.get("ENGINE_STATE") not in STOPPED_STATES


class CesarRemoteStartSensor(CesarBaseEntity, BinarySensorEntity):
    def __init__(self, coordinator: CesarSmartCoordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry, "Remote Start by Phone", "remote_start_by_phone")
        self._attr_entity_registry_enabled_default = False

    @property
    def is_on(self):
        statuses = self.coordinator.data.get("statuses", {})
        return statuses.get("REM_START_BY_PHONE") == "ON"
