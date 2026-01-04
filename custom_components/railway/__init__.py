"""The Railway integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RailwayApiClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN_TYPE,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .coordinator import RailwayDataUpdateCoordinator

if TYPE_CHECKING:
    from typing import TypeAlias

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

RailwayConfigEntry: TypeAlias = ConfigEntry[RailwayDataUpdateCoordinator]


def _get_scan_interval(entry: ConfigEntry) -> timedelta:
    """Get the scan interval from config entry options."""
    scan_minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    # Handle string values from selector
    if isinstance(scan_minutes, str):
        scan_minutes = int(scan_minutes)
    return timedelta(minutes=scan_minutes)


async def async_setup_entry(hass: HomeAssistant, entry: RailwayConfigEntry) -> bool:
    """Set up Railway from a config entry."""
    session = async_get_clientsession(hass)
    token_type = entry.data.get(CONF_TOKEN_TYPE, "personal")
    client = RailwayApiClient(entry.data[CONF_API_TOKEN], session, token_type)

    scan_interval = _get_scan_interval(entry)
    coordinator = RailwayDataUpdateCoordinator(hass, client, entry, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: RailwayConfigEntry) -> None:
    """Handle options update."""
    coordinator: RailwayDataUpdateCoordinator = entry.runtime_data
    new_interval = _get_scan_interval(entry)

    if coordinator.update_interval != new_interval:
        _LOGGER.debug("Updating scan interval to %s", new_interval)
        coordinator.update_interval = new_interval
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: RailwayConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: RailwayConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
