"""Sensors for PinPaw pets (battery level, tracking mode)."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinPawConfigEntry
from .const import TRACKING_MODES
from .entity import PinPawEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinPawConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for pet_id in coordinator.data:
        entities.append(PinPawBatterySensor(coordinator, pet_id))
        entities.append(PinPawTrackingModeSensor(coordinator, pet_id))
    async_add_entities(entities)


class PinPawBatterySensor(PinPawEntity, SensorEntity):
    """Battery level (%) of the tracker."""

    _attr_translation_key = "battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id)
        self._attr_unique_id = f"{pet_id}_battery"

    @property
    def native_value(self) -> int | None:
        level = self.position.get("batteryLevel")
        return int(level) if level is not None else None


class PinPawTrackingModeSensor(PinPawEntity, SensorEntity):
    """Which reporting schedule the tracker is on.

    Read-only because the three values are not reached the same way: live and
    daily are switch and command, while sleeping is one-way and lives behind
    its own button.
    """

    _attr_translation_key = "tracking_mode"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [mode.lower() for mode in TRACKING_MODES]

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id)
        self._attr_unique_id = f"{pet_id}_tracking_mode"

    @property
    def native_value(self) -> str | None:
        mode = self.pet.get("trackingMode")
        return mode.lower() if isinstance(mode, str) else None
