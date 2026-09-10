"""Switches for the modes and hardware a PinPaw tracker exposes.

Car mode and walk recording are backend state, flipped through their own
endpoints. Live tracking, LED and sound are device commands: the switch sends
one and the authoritative state arrives with the next poll.
"""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinPawConfigEntry
from .api import PinPawApiError
from .const import (
    CMD_DEFAULT_TRACKING,
    CMD_LED_OFF,
    CMD_LED_ON,
    CMD_LIVE_TRACKING,
    CMD_SOUND_OFF,
    CMD_SOUND_ON,
    TRACKING_MODE_LIVE,
    WALK_MODE_MANUAL,
)
from .entity import PinPawEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinPawConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []

    for pet_id, pet in coordinator.data.items():
        commands = pet.get("availableCommands") or []
        entities.append(PinPawCarModeSwitch(coordinator, pet_id))
        entities.append(PinPawWalkActiveSwitch(coordinator, pet_id))
        if CMD_LIVE_TRACKING in commands:
            entities.append(PinPawLiveTrackingSwitch(coordinator, pet_id))
        if CMD_LED_ON in commands:
            entities.append(PinPawLedSwitch(coordinator, pet_id))
        if CMD_SOUND_ON in commands:
            entities.append(PinPawSoundSwitch(coordinator, pet_id))

    async_add_entities(entities)


class PinPawSwitch(PinPawEntity, SwitchEntity):
    """Base switch: turns a write into a refresh, and API errors into HA errors."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator, pet_id: int, key: str) -> None:
        super().__init__(coordinator, pet_id)
        self._attr_translation_key = key
        self._attr_unique_id = f"{pet_id}_{key}"

    async def _apply(self, enabled: bool) -> None:
        """Perform the write. Subclasses implement the endpoint they need."""
        raise NotImplementedError

    async def _async_write(self, enabled: bool) -> None:
        try:
            await self._apply(enabled)
        except PinPawApiError as err:
            raise HomeAssistantError(f"PinPaw rejected the request: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_write(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_write(False)


class PinPawCarModeSwitch(PinPawSwitch):
    """Car mode: the tracker is riding along, so no walk is recorded."""

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id, "car_mode")

    @property
    def is_on(self) -> bool | None:
        return self.pet.get("carMode")

    async def _apply(self, enabled: bool) -> None:
        await self.coordinator.client.async_set_car_mode(self._pet_id, enabled)


class PinPawWalkActiveSwitch(PinPawSwitch):
    """Start and stop a walk by hand.

    The backend refuses this in automatic mode, where recording is always on
    and not the user's to control, so the switch reports itself unavailable
    there rather than offering a toggle that returns 400.
    """

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id, "walk_active")

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.pet.get("walkRecordingMode") == WALK_MODE_MANUAL
        )

    @property
    def is_on(self) -> bool | None:
        return self.pet.get("walkActive")

    async def _apply(self, enabled: bool) -> None:
        await self.coordinator.client.async_set_walk_active(self._pet_id, enabled)


class PinPawLiveTrackingSwitch(PinPawSwitch):
    """Live tracking on, or back to the daily reporting schedule.

    Off deliberately means "default tracking" rather than "sleeping": sleeping
    mode cannot be left over the API, so it gets its own button instead.
    """

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id, "live_tracking")

    @property
    def is_on(self) -> bool | None:
        mode = self.pet.get("trackingMode")
        return None if mode is None else mode == TRACKING_MODE_LIVE

    async def _apply(self, enabled: bool) -> None:
        await self.coordinator.client.async_send_command(
            self._pet_id, CMD_LIVE_TRACKING if enabled else CMD_DEFAULT_TRACKING
        )


class PinPawLedSwitch(PinPawSwitch):
    """The tracker's locator light."""

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id, "led")

    @property
    def is_on(self) -> bool | None:
        return self.device_state.get("lightSwitch")

    async def _apply(self, enabled: bool) -> None:
        await self.coordinator.client.async_send_command(
            self._pet_id, CMD_LED_ON if enabled else CMD_LED_OFF
        )


class PinPawSoundSwitch(PinPawSwitch):
    """The tracker's locator buzzer."""

    def __init__(self, coordinator, pet_id: int) -> None:
        super().__init__(coordinator, pet_id, "sound")

    @property
    def is_on(self) -> bool | None:
        return self.device_state.get("soundSwitch")

    async def _apply(self, enabled: bool) -> None:
        await self.coordinator.client.async_send_command(
            self._pet_id, CMD_SOUND_ON if enabled else CMD_SOUND_OFF
        )
