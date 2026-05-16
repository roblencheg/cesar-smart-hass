from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_SENSORS, MANUFACTURER, device_id_from_vin_unit
from .coordinator import CesarSmartCoordinator

_LOGGER = logging.getLogger(__name__)

FUEL_UNIT_MAP = {"LITER": UnitOfVolume.LITERS}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator: CesarSmartCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for source_key, config in STATUS_SENSORS.items():
        entities.append(CesarStatusSensor(coordinator, entry, source_key, config))

    entities.append(CesarLastUpdateSensor(coordinator, entry))
    entities.append(CesarLocationSpeedSensor(coordinator, entry))
    entities.append(CesarLocationCourseSensor(coordinator, entry))
    entities.append(CesarSimBalanceSensor(coordinator, entry))

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


class CesarStatusSensor(CesarBaseEntity, SensorEntity):
    def __init__(
        self,
        coordinator: CesarSmartCoordinator,
        entry: ConfigEntry,
        source_key: str,
        config: dict,
    ):
        super().__init__(coordinator, entry, config["name"], source_key)
        self._source_key = source_key
        self._attr_icon = config.get("icon")
        self._attr_entity_category = (
            EntityCategory.DIAGNOSTIC if config.get("disabled_by_default") else None
        )
        self._attr_entity_registry_enabled_default = not config.get("disabled_by_default", False)

        unit = config.get("unit")
        if unit == "°C":
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif unit == "V":
            self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        elif unit == "km":
            self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        else:
            self._attr_native_unit_of_measurement = unit

        if config.get("device_class"):
            self._attr_device_class = config["device_class"]
        if config.get("state_class"):
            self._attr_state_class = config["state_class"]

    @property
    def native_value(self):
        statuses = self.coordinator.data.get("statuses", {})
        val = statuses.get(self._source_key)
        if self._source_key == "FUEL_VALUE":
            fuel_type = statuses.get("FUEL_TYPE", "LITER")
            self._attr_native_unit_of_measurement = FUEL_UNIT_MAP.get(fuel_type, "%")
        return val


class CesarLastUpdateSensor(CesarBaseEntity, SensorEntity):
    def __init__(self, coordinator: CesarSmartCoordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry, "Last Update", "last_update")
        self._attr_device_class = "timestamp"

    @property
    def native_value(self):
        return self.coordinator.last_update


class CesarLocationSpeedSensor(CesarBaseEntity, SensorEntity):
    def __init__(self, coordinator: CesarSmartCoordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry, "Location Speed", "location_speed")
        self._attr_device_class = "speed"
        self._attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self):
        loc = self.coordinator.data.get("location")
        if loc:
            return loc.get("speedKm")
        return None


class CesarLocationCourseSensor(CesarBaseEntity, SensorEntity):
    def __init__(self, coordinator: CesarSmartCoordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry, "Location Course", "location_course")
        self._attr_native_unit_of_measurement = "°"
        self._attr_icon = "mdi:compass"
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        loc = self.coordinator.data.get("location")
        if loc:
            return loc.get("course")
        return None


class CesarSimBalanceSensor(CesarBaseEntity, SensorEntity):
    def __init__(self, coordinator: CesarSmartCoordinator, entry: ConfigEntry):
        super().__init__(coordinator, entry, "SIM Balance", "sim_balance")
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        return None
