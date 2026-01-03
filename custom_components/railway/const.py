"""Constants for the Railway integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "railway"

# Railway API
RAILWAY_API_ENDPOINT: Final = "https://backboard.railway.com/graphql/v2"

# Configuration
CONF_API_TOKEN: Final = "api_token"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=15)

# Attributes
ATTR_ACCOUNT_ID: Final = "account_id"
ATTR_ACCOUNT_NAME: Final = "account_name"
ATTR_ACCOUNT_EMAIL: Final = "account_email"
ATTR_PROJECT_ID: Final = "project_id"
ATTR_PROJECT_NAME: Final = "project_name"
ATTR_ENVIRONMENT_ID: Final = "environment_id"
ATTR_SERVICE_ID: Final = "service_id"
ATTR_DEPLOYMENT_ID: Final = "deployment_id"

# Entity keys
SENSOR_CREDIT_BALANCE: Final = "credit_balance"
SENSOR_ESTIMATED_USAGE: Final = "estimated_usage"
SENSOR_PROJECTS_COUNT: Final = "projects_count"
SENSOR_PROJECT_USAGE: Final = "project_usage"
BINARY_SENSOR_API_CONNECTED: Final = "api_connected"
