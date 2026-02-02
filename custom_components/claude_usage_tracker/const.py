"""Constants for Claude Usage integration."""

DOMAIN = "claude_usage_tracker"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_API_KEY = "api_key"
CONF_USE_SSL = "use_ssl"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_PORT = 8383
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_USE_SSL = False

# Sensor types
SENSOR_SESSION_USED = "session_used"
SENSOR_SESSION_LIMIT = "session_limit"
SENSOR_SESSION_PERCENTAGE = "session_percentage"
SENSOR_SESSION_REMAINING = "session_remaining"
SENSOR_SESSION_ACTIVE = "session_active"
SENSOR_SESSION_BURN_RATE = "session_burn_rate"
SENSOR_WEEKLY_USED = "weekly_used"
SENSOR_WEEKLY_LIMIT = "weekly_limit"
SENSOR_WEEKLY_PERCENTAGE = "weekly_percentage"
SENSOR_WEEKLY_REMAINING = "weekly_remaining"
