"""DataUpdateCoordinator for Railway integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RailwayApiClient, RailwayAuthError, RailwayApiError, RailwayConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RailwayDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Railway data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: RailwayApiClient,
        config_entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            config_entry=config_entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Railway API."""
        try:
            return await self.client.async_get_all_data()
        except RailwayAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except RailwayConnectionError as err:
            raise ConfigEntryNotReady(f"Connection to Railway failed: {err}") from err
        except RailwayApiError as err:
            raise UpdateFailed(f"Error communicating with Railway API: {err}") from err
