"""Binary sensor platform for Railway integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RailwayConfigEntry
from .const import DOMAIN
from .coordinator import RailwayDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RailwayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Railway binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []

    # API connected sensor
    entities.append(RailwayApiConnectedSensor(coordinator, entry))

    # Per-project deployment health sensors
    if coordinator.data:
        for project in coordinator.data.get("projects", []):
            project_id = project.get("id")
            project_name = project.get("name", "Unknown")

            if project_id:
                entities.append(
                    RailwayProjectHealthSensor(
                        coordinator=coordinator,
                        entry=entry,
                        project_id=project_id,
                        project_name=project_name,
                    )
                )

    async_add_entities(entities)


class RailwayApiConnectedSensor(
    CoordinatorEntity[RailwayDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor indicating API connection status."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "api_connected"

    def __init__(
        self,
        coordinator: RailwayDataUpdateCoordinator,
        entry: RailwayConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['account_id']}_api_connected"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["account_id"])},
            name=f"Railway ({entry.data.get('account_name', 'Account')})",
            manufacturer="Railway",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://railway.com",
        )

    @property
    def is_on(self) -> bool:
        """Return True if connected to Railway API."""
        return self.coordinator.last_update_success and bool(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        me = self.coordinator.data.get("me", {})
        return {
            "account_id": me.get("id"),
            "account_name": me.get("name"),
            "account_email": me.get("email"),
        }


class RailwayProjectHealthSensor(
    CoordinatorEntity[RailwayDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor for project deployment health."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_translation_key = "project_healthy"

    # Deployment statuses that indicate healthy/running state
    HEALTHY_STATUSES = {"SUCCESS", "RUNNING", "DEPLOYING"}

    def __init__(
        self,
        coordinator: RailwayDataUpdateCoordinator,
        entry: RailwayConfigEntry,
        project_id: str,
        project_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._project_id = project_id
        self._project_name = project_name
        self._attr_unique_id = f"{entry.data['account_id']}_project_{project_id}_health"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"project_{project_id}")},
            name=f"Railway Project: {project_name}",
            manufacturer="Railway",
            entry_type=DeviceEntryType.SERVICE,
            via_device=(DOMAIN, entry.data["account_id"]),
        )
        self._attr_translation_placeholders = {"project_name": project_name}

    @property
    def is_on(self) -> bool | None:
        """Return True if all deployments are healthy."""
        if not self.coordinator.data:
            return None

        deployments = self.coordinator.data.get("deployments", {}).get(
            self._project_id, []
        )

        if not deployments:
            # No deployments means no services or no data
            return None

        # Check if all latest deployments have healthy status
        return all(
            dep.get("status", "").upper() in self.HEALTHY_STATUSES
            for dep in deployments
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        deployments = self.coordinator.data.get("deployments", {}).get(
            self._project_id, []
        )

        attrs = {
            "project_id": self._project_id,
            "project_name": self._project_name,
            "deployment_count": len(deployments),
        }

        if deployments:
            # Add details of latest deployments per service
            deployment_details = []
            for dep in deployments:
                deployment_details.append(
                    {
                        "service": dep.get("service_name"),
                        "status": dep.get("status"),
                        "created_at": dep.get("createdAt"),
                    }
                )
            attrs["deployments"] = deployment_details

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available or not self.coordinator.data:
            return False
        # Available if we have deployment data for this project
        return self._project_id in self.coordinator.data.get("deployments", {})
