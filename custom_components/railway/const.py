"""Constants for the Railway integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "railway"

# Railway API
RAILWAY_API_ENDPOINT: Final = "https://backboard.railway.com/graphql/v2"

# Configuration
CONF_API_TOKEN: Final = "api_token"
CONF_TOKEN_TYPE: Final = "token_type"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=15)
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 15
