"""The PinPaw Pet Tracker integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PinPawClient
from .const import CONF_API_TOKEN, CONF_BASE_URL
from .coordinator import PinPawCoordinator

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON,
]

type PinPawConfigEntry = ConfigEntry[PinPawCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PinPawConfigEntry) -> bool:
    """Set up PinPaw from a config entry."""
    client = PinPawClient(
        base_url=entry.data[CONF_BASE_URL],
        api_token=entry.data[CONF_API_TOKEN],
        session=async_get_clientsession(hass),
    )
    coordinator = PinPawCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start push only after entities exist and the first REST refresh populated data.
    coordinator.start_websocket()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PinPawConfigEntry) -> bool:
    """Unload a config entry."""
    await entry.runtime_data.stop_websocket()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
