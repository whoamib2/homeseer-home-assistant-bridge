DOMAIN = "homeseer_bridge"

CONF_HS_URL = "homeseer_url"
CONF_MQTT_PREFIX = "mqtt_prefix"
CONF_EXCLUDED_TERMS = "excluded_terms"

DEFAULT_HS_URL = ""
DEFAULT_MQTT_PREFIX = ""
DEFAULT_EXCLUDED_TERMS = ""

PLATFORMS = ["switch", "light", "sensor", "binary_sensor", "lock", "cover", "fan"]

SIGNAL_STATE_UPDATED = "homeseer_bridge_state_updated"

CONF_ENABLE_DEBUG_LOGGING = "enable_debug_logging"
DEFAULT_ENABLE_DEBUG_LOGGING = False

CONF_REFRESH_INTERVAL_SECONDS = "refresh_interval_seconds"
DEFAULT_REFRESH_INTERVAL_SECONDS = 600

CONF_RECONNECT_INTERVAL_SECONDS = "reconnect_interval_seconds"
DEFAULT_RECONNECT_INTERVAL_SECONDS = 60

CONF_VIRTUAL_POLL_INTERVAL_SECONDS = "virtual_poll_interval_seconds"
DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS = 30

SIGNAL_NEW_DEVICES = "homeseer_bridge_new_devices"

CONF_ACTIVITY_EXCLUDED_TERMS = "activity_excluded_terms"
DEFAULT_ACTIVITY_EXCLUDED_TERMS = ""
