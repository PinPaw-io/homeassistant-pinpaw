"""Binary sensors for PinPaw pets: online, charging, battery low, lost, blocked."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinPawConfigEntry
from .const import LOW_BATTERY_THRESHOLD
from .entity import PinPawEntity


@dataclass(frozen=True, kw_only=True)
class PinPawBinaryDescription(BinarySensorEntityDescription):
    """Describes a PinPaw binary sensor and how to derive its state."""

    # Receives (pet, latestPosition) and returns the on/off state.
    is_on: Callable[[dict[str, Any], dict[str, Any]], bool | None]


SENSORS: tuple[PinPawBinaryDescription, ...] = (
    PinPawBinaryDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on=lambda pet, pos: (
            pet.get("deviceStatus") == "online"
            if pet.get("deviceStatus") is not None
            else pos.get("online")
        ),
    ),
    PinPawBinaryDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on=lambda pet, pos: pos.get("charging"),
    ),
    PinPawBinaryDescription(
        key="lost",
        translation_key="lost",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on=lambda pet, pos: pet.get("lost"),
    ),
    PinPawBinaryDescription(
        key="device_disabled",
        translation_key="device_disabled",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=False,
        is_on=lambda pet, pos: pet.get("deviceDisabled"),
    ),
    PinPawBinaryDescription(
        key="battery_low",
        translation_key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        is_on=lambda pet, pos: (
            pos.get("batteryLevel") is not None
            and pos["batteryLevel"] < LOW_BATTERY_THRESHOLD
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinPawConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        PinPawBinarySensor(coordinator, pet_id, description)
        for pet_id in coordinator.data
        for description in SENSORS
    )


class PinPawBinarySensor(PinPawEntity, BinarySensorEntity):
    """A single derived binary state for a pet."""

    entity_description: PinPawBinaryDescription

    def __init__(
        self, coordinator, pet_id: int, description: PinPawBinaryDescription
    ) -> None:
        super().__init__(coordinator, pet_id)
        self.entity_description = description
        self._attr_unique_id = f"{pet_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on(self.pet, self.position)
