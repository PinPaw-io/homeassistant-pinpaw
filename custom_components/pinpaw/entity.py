"""Shared base entity for PinPaw entities."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PinPawCoordinator


class PinPawEntity(CoordinatorEntity[PinPawCoordinator]):
    """Base class binding an entity to a single pet."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PinPawCoordinator, pet_id: int) -> None:
        super().__init__(coordinator)
        self._pet_id = pet_id

    @property
    def pet(self) -> dict[str, Any]:
        """Return the latest data for this pet (empty dict if it vanished)."""
        return self.coordinator.data.get(self._pet_id, {})

    @property
    def position(self) -> dict[str, Any]:
        """Return the pet's latest position payload."""
        return self.pet.get("latestPosition") or {}

    @property
    def device_state(self) -> dict[str, Any]:
        """Return the pet's last heartbeat snapshot (LED and sound state)."""
        return self.pet.get("deviceState") or {}

    def supports_command(self, command: str) -> bool:
        """Whether the tracker's protocol has a template for ``command``."""
        return command in (self.pet.get("availableCommands") or [])

    @property
    def available(self) -> bool:
        return super().available and self._pet_id in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        pet = self.pet
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._pet_id))},
            name=pet.get("name") or f"Pet {self._pet_id}",
            manufacturer="PinPaw",
            model="GPS Pet Tracker",
        )
