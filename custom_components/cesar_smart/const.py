import hashlib

from homeassistant.const import Platform

DOMAIN = "cesar_smart"
MANUFACTURER = "Cesar"


def device_id_from_vin_unit(vin: str, unit_id: str) -> str:
    raw = f"cesar_smart:{vin}:{unit_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
]

BASE_API_URL = "https://tw-cesar-key.csat.ru/"
OAUTH_API_URL = "https://tw-sso-authorization-server.csat.ru/tw-sso-authorization-server/"
WS_URL = "wss://tw-web-socket-gate.csat.ru/tw-web-socket-gate/push"

# Public OAuth mobile client credentials from official Cesar Smart APK BuildConfig.
# These are NOT user secrets — public client identifiers embedded in the app.
CLIENT_ID = "ma_cesar_key"
CLIENT_SECRET = "Aa123456"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ENABLE_WEBSOCKET = "enable_websocket"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LOCATION_INTERVAL = "location_interval"
CONF_DEVICE_ID = "device_id"
CONF_VIN = "vin"
CONF_UNIT_ID = "unit_id"
CONF_VEHICLE_NAME = "vehicle_name"
CONF_ENABLE_FULL_INFO = "enable_full_info"
CONF_FULL_INFO_INTERVAL = "full_info_interval"
CONF_FULL_INFO_MERGE_MODE = "full_info_merge_mode"
CONF_DEBUG_ATTRIBUTES = "debug_attributes"
CONF_ENABLE_BALANCE = "enable_balance"
CONF_BALANCE_INTERVAL = "balance_interval"

MERGE_MODE_PREFER_FULL_INFO = "prefer_full_info"
MERGE_MODE_PREFER_STATUSES = "prefer_statuses"
MERGE_MODE_FILL_MISSING_ONLY = "fill_missing_only"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_LOCATION_INTERVAL = 300
MIN_SCAN_INTERVAL = 30
MIN_LOCATION_INTERVAL = 60
MIN_FULL_INFO_INTERVAL = 60
DEFAULT_ENABLE_WEBSOCKET = True
DEFAULT_ENABLE_FULL_INFO = True
DEFAULT_FULL_INFO_INTERVAL = 300
DEFAULT_FULL_INFO_MERGE_MODE = MERGE_MODE_PREFER_FULL_INFO
DEFAULT_DEBUG_ATTRIBUTES = False
DEFAULT_ENABLE_BALANCE = True
DEFAULT_BALANCE_INTERVAL = 3600
MIN_BALANCE_INTERVAL = 300

TOKEN_EXPIRY_BUFFER = 30
WS_RECONNECT_DELAYS = [5, 15, 30, 60]

STATUS_SENSORS = {
    "ENGINE_STATE": {"name": "Engine State", "icon": "mdi:engine"},
    "MODE": {"name": "Security Mode", "icon": "mdi:shield-car"},
    "FUEL_VALUE": {
        "name": "Fuel Level",
        "icon": "mdi:fuel",
        "unit": None,
        "device_class": "volume",
        "state_class": "measurement",
    },
    "MILEAGE_KM": {
        "name": "Mileage",
        "icon": "mdi:counter",
        "unit": "km",
        "device_class": "distance",
        "state_class": "total_increasing",
    },
    "VEHICLE_CHARGE_VOLT": {
        "name": "Battery Voltage",
        "icon": "mdi:car-battery",
        "unit": "V",
        "device_class": "voltage",
        "state_class": "measurement",
    },
    "ENGINE_TEMP": {
        "name": "Engine Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "SALON_TEMP": {
        "name": "Cabin Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "OUTDOOR_TEMP": {
        "name": "Outdoor Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "L_SIDE_TEMP": {
        "name": "Left Side Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "disabled_by_default": True,
    },
    "R_SIDE_TEMP": {
        "name": "Right Side Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "disabled_by_default": True,
    },
    "LABEL": {"name": "Label", "icon": "mdi:tag"},
}

BINARY_SENSOR_MAP = {
    "IGNITION": {"name": "Ignition", "device_class": "power", "on_value": "ON"},
    "HOOD": {"name": "Hood", "device_class": "opening", "on_value": "OPEN"},
    "DOOR_FRONT_LEFT": {"name": "Door Front Left", "device_class": "door", "on_value": "OPEN"},
    "DOOR_FRONT_RIGHT": {"name": "Door Front Right", "device_class": "door", "on_value": "OPEN"},
    "DOOR_BACK_LEFT": {"name": "Door Back Left", "device_class": "door", "on_value": "OPEN"},
    "DOOR_BACK_RIGHT": {"name": "Door Back Right", "device_class": "door", "on_value": "OPEN"},
    "DOOR_BOOT": {"name": "Trunk", "device_class": "opening", "on_value": "OPEN"},
}

STOPPED_STATES = {"STOPPED", "OFF", None}
