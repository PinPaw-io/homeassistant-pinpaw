"""Buttons for the one-way device commands."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinPawConfigEntry
from .api import PinPawApiError
from .const import CMD_SAVING_TRACKING
from .entity import PinPawEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinPawConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        PinPawSleepButton(coordinator, pet_id)
        for pet_id, pet in coordinator.data.items()
        if CMD_SAVING_TRACKING in (pet.get("availableCommands") or [])
    )


class PinPawSleepButton(PinPawEntity, ButtonEntity):
    """Put the tracker into sleeping mode to save battery.

    A button rather than a switch on purpose: this is one-way. Waking a
    sleeping tracker happens over Bluetooth with the phone next to it, never
    through the API, so there is no "off" to offer. The ``Tracking mode``
    sensor shows when the device is asleep.
    """

    _attr_translation_key = "sleep_mode"

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id)
        self._attr_unique_id = f"{pet_id}_sleep_mode"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_send_command(
                self._pet_id, CMD_SAVING_TRACKING
            )
        except PinPawApiError as err:
            raise HomeAssistantError(f"PinPaw rejected the request: {err}") from err
        await self.coordinator.async_request_refresh()
