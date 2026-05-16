from __future__ import annotations

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import CesarSmartCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator: CesarSmartCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CesarDeviceTracker(coordinator, entry)])


class CesarDeviceTracker(CoordinatorEntity, TrackerEntity):
    def __init__(
        self,
        coordinator: CesarSmartCoordinator,
        entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.data.get("vehicle_name", "Cesar Smart Vehicle")
        self._attr_unique_id = f"{entry.entry_id}_tracker"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": self._attr_name,
            "manufacturer": MANUFACTURER,
            "model": "",
        }

    @property
    def source_type(self) -> str:
        return "gps"

    @property
    def latitude(self) -> float | None:
        loc = self.coordinator.data.get("location")
        if loc:
            return loc.get("latitude")
        return None

    @property
    def longitude(self) -> float | None:
        loc = self.coordinator.data.get("location")
        if loc:
            return loc.get("longitude")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        loc = self.coordinator.data.get("location")
        if loc:
            return {
                "speed": loc.get("speedKm"),
                "course": loc.get("course"),
            }
        return {}
