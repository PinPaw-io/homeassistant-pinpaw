"""Constants for the PinPaw integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "pinpaw"

# Config entry keys
CONF_BASE_URL = "base_url"
CONF_API_TOKEN = "api_token"
CONF_USE_WEBSOCKET = "use_websocket"

# Enable near real-time push via WebSocket in addition to REST polling.
DEFAULT_USE_WEBSOCKET = True

# A PinPaw personal access token always carries this prefix.
API_TOKEN_PREFIX = "ppw_pat_"

DEFAULT_BASE_URL = "https://api.pinpaw.io"

# How often the coordinator polls the backend for fresh pet state.
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

# Battery level (%) below which the "battery low" binary sensor turns on.
LOW_BATTERY_THRESHOLD = 20

# Tracking modes reported by the backend in ``trackingMode``.
TRACKING_MODE_LIVE = "TRACKING"
TRACKING_MODE_SLEEPING = "SAVING"
TRACKING_MODE_DAILY = "DAILY"
TRACKING_MODES = [TRACKING_MODE_LIVE, TRACKING_MODE_SLEEPING, TRACKING_MODE_DAILY]

# Walk recording modes reported by the backend in ``walkRecordingMode``.
WALK_MODE_AUTO = "AUTO"
WALK_MODE_MANUAL = "MANUAL"

# Device command types. Only the ones this integration sends are listed.
CMD_LIVE_TRACKING = "LIVE_TRACKING"
CMD_DEFAULT_TRACKING = "DEFAULT_TRACKING"
CMD_SAVING_TRACKING = "SAVING_TRACKING"
CMD_LED_ON = "LED_SWITCH_ON"
CMD_LED_OFF = "LED_SWITCH_OFF"
CMD_SOUND_ON = "SOUND_SWITCH_ON"
CMD_SOUND_OFF = "SOUND_SWITCH_OFF"
