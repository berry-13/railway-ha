"""The Railway integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RailwayApiClient
from .const import DOMAIN
from .coordinator import RailwayDataUpdateCoordinator

if TYPE_CHECKING:
    from typing import TypeAlias

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

RailwayConfigEntry: TypeAlias = ConfigEntry[RailwayDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: RailwayConfigEntry) -> bool:
    """Set up Railway from a config entry."""
    session = async_get_clientsession(hass)
    token_type = entry.data.get("token_type", "personal")
    client = RailwayApiClient(entry.data[CONF_API_TOKEN], session, token_type)

    coordinator = RailwayDataUpdateCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: RailwayConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: RailwayConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
