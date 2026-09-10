# PinPaw Pet Tracker — Home Assistant integration

Custom integration (HACS) for the [PinPaw](https://pinpaw.io) GPS pet tracker.

> **Status: working — experimental.** The integration runs against a live
> PinPaw backend — location, battery, charging, online status, the mode
> controls and the reporting-interval control all work in Home Assistant. It is still
> experimental, so bugs may surface; please report any issues.

## Features

| Entity | Platform | Source |
| --- | --- | --- |
| Location | `device_tracker` | `latestPosition.latitude/longitude` → works with HA Zones for geofencing |
| Battery | `sensor` (%) | `latestPosition.batteryLevel` |
| Online | `binary_sensor` (connectivity) | `deviceStatus` / `latestPosition.online` |
| Charging | `binary_sensor` | `latestPosition.charging` |
| Battery low | `binary_sensor` | `batteryLevel < 20%` (configurable in `const.py`) |
| Reported lost | `binary_sensor` (problem) | `lost` |
| Tracker blocked | `binary_sensor` (problem, disabled by default) | `deviceDisabled` |
| Tracking mode | `sensor` (enum: live / sleeping / daily) | `trackingMode` |
| Reporting interval | `number` (s) | `PUT /api/pets/{id}/tracking-interval` |
| Car mode | `switch` | `PUT /api/pets/{id}/car-mode` |
| Walk recording mode | `select` (automatic / manual) | `PUT /api/pets/{id}/walk-recording-mode` |
| Walk recording | `switch` | `PUT /api/pets/{id}/walk-active` |
| Live tracking | `switch` | `LIVE_TRACKING` / `DEFAULT_TRACKING` command |
| Sleeping mode | `button` | `SAVING_TRACKING` command |
| Light | `switch` | `LED_SWITCH_ON/OFF` command, state from `/api/device-states/my-pets` |
| Sound | `switch` | `SOUND_SWITCH_ON/OFF` command, state from `/api/device-states/my-pets` |

Geofencing is intentionally **not** implemented here: exposing the pet as a
`device_tracker` lets Home Assistant's native Zones + automations handle it.

### Modes

**Walk recording** decides how walks get recorded. In *automatic* mode the
tracker records continuously and the `Walk recording` switch is unavailable,
because recording is not the user's to control there. In *manual* mode the
switch starts and stops each walk by hand.

**Car mode** suspends walk recording while the pet is riding along, so a drive
does not land in the history as a very fast walk. Switching walk recording to
manual clears car mode, which the backend does because a manual walk has no
trip detection left for car mode to suppress.

**Sleeping mode** is a button, not a switch, because it is one-way: waking a
sleeping tracker happens over Bluetooth with the phone next to it and cannot be
done through the API. The `Tracking mode` sensor shows when a device is asleep.

**Light and sound** are only created for trackers whose protocol advertises
them (`availableCommands`). Their state comes from the tracker's last
heartbeat, so it can lag a few seconds behind the command.

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
- The LED and sound state lives only in `GET /api/device-states/my-pets`, which
  is polled alongside `/api/pets` — but only when at least one tracker on the
  account advertises those commands, so accounts that cannot use them pay no
  extra request.
- Commands are sent through the fire-and-forget endpoint rather than its
  `/sync` variant, which blocks for up to 30 s waiting for the tracker to
  acknowledge. The resulting state arrives with the next poll.

## Layout

```
custom_components/pinpaw/
├── __init__.py          # setup / unload, platform list
├── api.py               # async REST client (Bearer PAT)
├── config_flow.py       # token + server URL setup
├── const.py             # domain, defaults, thresholds
├── coordinator.py       # polls /api/pets (+ /api/device-states), merges push
├── websocket.py         # optional real-time push listener
├── entity.py            # shared base entity + device info
├── device_tracker.py    # GPS location
├── sensor.py            # battery %, tracking mode
├── binary_sensor.py     # online / charging / battery low / lost / blocked
├── number.py            # reporting interval control
├── switch.py            # car mode, walk recording, live tracking, light, sound
├── select.py            # walk recording mode (automatic / manual)
├── button.py            # sleeping mode (one-way)
├── manifest.json
├── strings.json
└── translations/        # en, pl
```

## License

[MIT](LICENSE) © PinPaw.pl
