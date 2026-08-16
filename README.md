# PinPaw Pet Tracker — Home Assistant integration

Custom integration (HACS) for the [PinPaw](https://pinpaw.io) GPS pet tracker.

> **Status: working — experimental.** The integration runs against a live
> PinPaw backend — location, battery, charging, online status and the
> reporting-interval control are all verified in Home Assistant. It is still
> experimental, so bugs may surface; please report any issues.

## Features

| Entity | Platform | Source |
| --- | --- | --- |
| Location | `device_tracker` | `latestPosition.latitude/longitude` → works with HA Zones for geofencing |
| Battery | `sensor` (%) | `latestPosition.batteryLevel` |
| Online | `binary_sensor` (connectivity) | `deviceStatus` / `latestPosition.online` |
| Charging | `binary_sensor` | `latestPosition.charging` |
| Battery low | `binary_sensor` | `batteryLevel < 20%` (configurable in `const.py`) |
| Reporting interval | `number` (s) | `PUT /api/pets/{id}/tracking-interval` |

Geofencing is intentionally **not** implemented here: exposing the pet as a
`device_tracker` lets Home Assistant's native Zones + automations handle it.

## Installation (HACS)

1. HACS → Integrations → ⋮ → **Custom repositories**.
2. Add `https://github.com/PinPaw-io/homeassistant-pinpaw`, category
   **Integration**.
3. Install **PinPaw Pet Tracker**, restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → *PinPaw*.

> `PinPaw-io/homeassistant-pinpaw` is the canonical repository — please open
> issues and pull requests there. A mirror is kept at
> [`PinPaw-pl/homeassistant-pinpaw`](https://github.com/PinPaw-pl/homeassistant-pinpaw).

## Authentication

The integration authenticates with a **personal access token** (no password
stored in Home Assistant).

1. In the PinPaw app: **Settings → API tokens → Create token**.
2. Copy the token (shown once — it starts with `ppw_pat_`).
3. Paste it into the integration's setup dialog, together with the server URL.

Tokens are long-lived and can be revoked at any time from the app, which
immediately cuts off this integration's access.

## Reconfiguring

To change the server URL, API token or the real-time (WebSocket) setting after
setup, go to **Settings → Devices & Services → PinPaw → ⋮ → Reconfigure**. The
new token must belong to the same PinPaw account; the entities are kept.

## Brand images (logo)

The PinPaw icon and logo ship with the integration in
`custom_components/pinpaw/brand/` (`icon.png` 256×256, `icon@2x.png` 512×512,
`logo.png`, `logo@2x.png`). Since Home Assistant 2026.3, custom integrations
serve their own brand images locally and they take priority over the brands
CDN — no `home-assistant/brands` submission is needed. On older Home Assistant
versions the default icon is shown instead.

## Notes / things to verify against the live API

- `online` status is derived by the backend from position freshness (< 5 min),
  not a true heartbeat — a device on a long reporting interval may read offline.
- Location updates arrive two ways: REST polling of `GET /api/pets` every 30 s
  (`const.py`, authoritative) **and** an optional WebSocket push
  (`/api/socket?jwt=<token>`) for near real-time coordinates. The push is
  enabled by default and can be turned off during setup. Pushed frames that
  carry a `petId` are applied instantly; other frames trigger a debounced REST
  refresh instead.

## Layout

```
custom_components/pinpaw/
├── __init__.py          # setup / unload, platform list
├── api.py               # async REST client (Bearer PAT)
├── config_flow.py       # token + server URL setup
├── const.py             # domain, defaults, thresholds
├── coordinator.py       # polls /api/pets, indexes by pet id, merges push
├── websocket.py         # optional real-time push listener
├── entity.py            # shared base entity + device info
├── device_tracker.py    # GPS location
├── sensor.py            # battery %
├── binary_sensor.py     # online / charging / battery low
├── number.py            # reporting interval control
├── manifest.json
├── strings.json
└── translations/        # en, pl
```

## License

[MIT](LICENSE) © PinPaw.pl
