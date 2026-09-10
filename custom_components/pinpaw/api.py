"""Thin async client for the PinPaw public API.

Only the endpoints needed by the Home Assistant integration are wrapped.
Authentication uses a long-lived personal access token (``ppw_pat_…``)
sent as a Bearer credential.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class PinPawApiError(Exception):
    """Generic API failure."""


class PinPawAuthError(PinPawApiError):
    """Raised when the token is rejected (HTTP 401/403)."""


class PinPawClient:
    """Minimal client wrapping the PinPaw REST API."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = api_token
        self._session = session

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(
                method, url, headers=self._headers, **kwargs
            ) as resp:
                if resp.status in (401, 403):
                    raise PinPawAuthError(f"Authentication failed ({resp.status})")
                if resp.status >= 400:
                    body = await resp.text()
                    raise PinPawApiError(f"{method} {path} -> {resp.status}: {body}")
                if resp.status == 204:
                    return None
                return await resp.json()
        except aiohttp.ClientError as err:
            raise PinPawApiError(f"Network error calling {path}: {err}") from err

    async def async_validate(self) -> dict[str, Any]:
        """Verify the token by fetching the current user. Used by config flow."""
        return await self._request("GET", "/api/auth/me")

    async def async_get_pets(self) -> list[dict[str, Any]]:
        """Return all pets with device status, latest position and interval.

        ``GET /api/pets`` already includes ``deviceStatus``, ``latestPosition``
        (lat/lon, batteryLevel, charging, online) and ``trackingInterval``.
        """
        return await self._request("GET", "/api/pets")

    async def async_set_tracking_interval(self, pet_id: int, seconds: int) -> None:
        """Push a new reporting interval to the device."""
        await self._request(
            "PUT",
            f"/api/pets/{pet_id}/tracking-interval",
            json={"trackingInterval": seconds},
        )

    async def async_get_device_states(self) -> list[dict[str, Any]]:
        """Return the last heartbeat snapshot for every visible pet.

        ``GET /api/device-states/my-pets`` is the only place the LED and sound
        state lives; ``/api/pets`` does not carry it. Devices that have never
        sent a heartbeat are simply absent from the list.
        """
        return await self._request("GET", "/api/device-states/my-pets")

    async def async_set_car_mode(self, pet_id: int, enabled: bool) -> None:
        """Enable or disable car mode (walk recording suspended while driving)."""
        await self._request(
            "PUT", f"/api/pets/{pet_id}/car-mode", json={"enabled": enabled}
        )

    async def async_set_walk_recording_mode(self, pet_id: int, mode: str) -> None:
        """Switch walk recording between ``AUTO`` and ``MANUAL``.

        Switching to ``AUTO`` starts recording immediately; switching to
        ``MANUAL`` stops it and clears car mode.
        """
        await self._request(
            "PUT", f"/api/pets/{pet_id}/walk-recording-mode", json={"mode": mode}
        )

    async def async_set_walk_active(self, pet_id: int, enabled: bool) -> None:
        """Start or stop walk recording. Only valid in ``MANUAL`` mode."""
        await self._request(
            "PUT", f"/api/pets/{pet_id}/walk-active", json={"enabled": enabled}
        )

    async def async_send_command(self, pet_id: int, command: str) -> None:
        """Send a device command without waiting for the tracker to acknowledge it.

        The backend also offers a ``/sync`` variant that blocks for up to 30
        seconds waiting for the device's reply. Home Assistant only needs the
        command to leave the building, and the authoritative state arrives with
        the next poll, so the fire-and-forget endpoint is used instead.
        """
        await self._request("POST", f"/api/pets/{pet_id}/commands/{command}")
