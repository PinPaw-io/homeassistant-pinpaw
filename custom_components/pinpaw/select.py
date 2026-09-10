"""Select entity for the walk recording mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinPawConfigEntry
from .api import PinPawApiError
from .const import WALK_MODE_AUTO, WALK_MODE_MANUAL
from .entity import PinPawEntity

# HA options are lower case by convention; the API speaks the enum names.
_TO_API = {"auto": WALK_MODE_AUTO, "manual": WALK_MODE_MANUAL}
_FROM_API = {value: key for key, value in _TO_API.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinPawConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        PinPawWalkModeSelect(coordinator, pet_id) for pet_id in coordinator.data
    )


class PinPawWalkModeSelect(PinPawEntity, SelectEntity):
    """Automatic walk detection, or walks started and stopped by hand.

    Picking automatic starts recording straight away. Picking manual stops it
    and clears car mode, which the backend does because a manual walk has no
    trip detection for car mode to suppress.
    """

    _attr_translation_key = "walk_recording_mode"
    _attr_options = list(_TO_API)

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id)
        self._attr_unique_id = f"{pet_id}_walk_recording_mode"

    @property
    def current_option(self) -> str | None:
        return _FROM_API.get(self.pet.get("walkRecordingMode"))

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.client.async_set_walk_recording_mode(
                self._pet_id, _TO_API[option]
            )
        except PinPawApiError as err:
            raise HomeAssistantError(f"PinPaw rejected the request: {err}") from err
        await self.coordinator.async_request_refresh()
