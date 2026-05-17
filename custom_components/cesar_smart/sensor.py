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

from .const import DOMAIN, MANUFACTURER, STATUS_SENSORS, device_id_from_vin_unit
from .coordinator import CesarSmartCoordinator
from .data_extractors import (
    extract_balance_communication_service,
    extract_balance_currency,
    extract_balance_phone,
    extract_balance_unit_class,
    extract_balance_unit_id,
    extract_balance_updated_at,
    extract_balance_value,
    extract_statuses_from_full_info,
    redact_phone,
    redact_sensitive_balance,
    redact_unit_id,
)

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
        if unit == "\u00b0C":
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

    @property
    def extra_state_attributes(self) -> dict | None:
        debug = self.coordinator._debug_attributes
        if not debug:
            return None

        data = self.coordinator.data or {}
        statuses_raw = data.get("statuses_raw", {})
        full_info = data.get("full_info")

        attrs: dict = {
            "source_key": self._source_key,
            "coordinator_last_update": self.coordinator.last_update,
            "raw_status_value": statuses_raw.get(self._source_key),
        }

        extracted_full = extract_statuses_from_full_info(full_info) if full_info else {}
        attrs["full_info_value"] = extracted_full.get(self._source_key)

        if self._source_key in (data.get("statuses") or {}):
            raw = statuses_raw.get(self._source_key)
            merged = data["statuses"].get(self._source_key)
            if raw != merged:
                attrs["source"] = "full_info_merged"

        return attrs


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
        self._attr_native_unit_of_measurement = "\u00b0"
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
        self._attr_icon = "mdi:sim"
        self._attr_native_unit_of_measurement = "\u20bd"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        balance = data.get("balance")
        value = extract_balance_value(balance)
        if value is not None:
            return value
        balance_raw = data.get("balance_raw")
        return extract_balance_value(balance_raw)

    @property
    def extra_state_attributes(self) -> dict | None:
        data = self.coordinator.data or {}
        balance = data.get("balance")
        balance_raw = data.get("balance_raw")
        source = balance if balance is not None else balance_raw
        attrs: dict = {
            "currency": extract_balance_currency(source) or "RUB",
            "updated_at": extract_balance_updated_at(source),
            "phone": redact_phone(extract_balance_phone(source)),
            "unit_id": redact_unit_id(extract_balance_unit_id(source)),
            "unit_class": extract_balance_unit_class(source),
            "communication_service": extract_balance_communication_service(source),
            "has_balance_data": balance is not None,
            "balance_type": type(balance).__name__ if balance is not None else "None",
            "parsed_value": extract_balance_value(source),
        }
        if self.coordinator._debug_attributes:
            attrs["raw_balance_type"] = type(balance).__name__ if balance is not None else "None"
            attrs["raw_balance"] = redact_sensitive_balance(balance)
            attrs["raw_balance_response"] = redact_sensitive_balance(balance_raw)
        return {k: v for k, v in attrs.items() if v is not None}
