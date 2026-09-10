"""Data update coordinator polling the PinPaw backend.

Location data arrives two ways:
- REST polling every ``DEFAULT_SCAN_INTERVAL`` (authoritative, complete state).
- Optional WebSocket push (near real-time) that optimistically updates
  coordinates and triggers a debounced REST refresh for authoritative state.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PinPawApiError, PinPawAuthError, PinPawClient
from .const import (
    CMD_LED_ON,
    CMD_SOUND_ON,
    CONF_API_TOKEN,
    CONF_BASE_URL,
    CONF_USE_WEBSOCKET,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_WEBSOCKET,
    DOMAIN,
)
from .websocket import PinPawWebSocket

_LOGGER = logging.getLogger(__name__)

# Position fields copied verbatim from a pushed frame into ``latestPosition``.
_PUSH_FIELDS = ("latitude", "longitude", "batteryLevel", "charging", "online")

# A pet gets the extra device-state fetch only if its tracker actually has the
# hardware behind them; ``availableCommands`` is per device protocol.
_DEVICE_STATE_COMMANDS = (CMD_LED_ON, CMD_SOUND_ON)


class PinPawCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Fetches all pets once per interval and indexes them by pet id."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: PinPawClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self.client = client
        self._ws: PinPawWebSocket | None = None

        if entry.data.get(CONF_USE_WEBSOCKET, DEFAULT_USE_WEBSOCKET):
            self._ws = PinPawWebSocket(
                base_url=entry.data[CONF_BASE_URL],
                token=entry.data[CONF_API_TOKEN],
                session=async_get_clientsession(hass),
                on_message=self._handle_push,
            )

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            pets = await self.client.async_get_pets()
        except PinPawAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except PinPawApiError as err:
            raise UpdateFailed(f"Error fetching PinPaw data: {err}") from err

        indexed = {pet["id"]: pet for pet in pets if "id" in pet}
        await self._merge_device_states(indexed)
        return indexed

    async def _merge_device_states(self, pets: dict[int, dict[str, Any]]) -> None:
        """Attach the LED/sound heartbeat snapshot under ``deviceState``.

        Skipped entirely when no tracker on the account advertises the LED or
        sound commands, so accounts that cannot use them pay no extra request.
        A failure here is not fatal: the pet data is already in hand, and the
        LED and sound switches simply read as unknown until the next poll.
        """
        if not any(
            command in (pet.get("availableCommands") or [])
            for pet in pets.values()
            for command in _DEVICE_STATE_COMMANDS
        ):
            return

        try:
            states = await self.client.async_get_device_states()
        except PinPawApiError as err:
            _LOGGER.debug("Could not fetch PinPaw device states: %s", err)
            return

        for state in states:
            pet = pets.get(state.get("petId"))
            if pet is not None:
                pet["deviceState"] = state

    def start_websocket(self) -> None:
        """Start the push listener (call after the first REST refresh)."""
        if self._ws:
            self._ws.start()

    async def stop_websocket(self) -> None:
        if self._ws:
            await self._ws.stop()

    async def _handle_push(self, payload: dict[str, Any]) -> None:
        """Apply a pushed ``{"positions": [...]}`` frame.

        Frames carrying ``petId`` (PinPaw's normalised shape) are merged in
        place for instant updates. Anything else — frames without a ``petId`` —
        falls back to a debounced authoritative refresh.
        """
        if not self.data:
            return

        positions = payload.get("positions") or []
        updated = False
        needs_refresh = False

        for pos in positions:
            pet_id = pos.get("petId")
            if pet_id in self.data:
                self.data[pet_id].setdefault("latestPosition", {}).update(
                    {k: pos[k] for k in _PUSH_FIELDS if k in pos}
                )
                updated = True
            else:
                # Unknown shape (no petId) — let REST reconcile.
                needs_refresh = True

        if updated:
            self.async_set_updated_data(self.data)
        if needs_refresh:
            await self.async_request_refresh()
