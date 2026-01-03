"""Sensor platform for Railway integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RailwayConfigEntry
from .const import DOMAIN
from .coordinator import RailwayDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class RailwaySensorEntityDescription(SensorEntityDescription):
    """Describes Railway sensor entity."""

    value_fn: Callable[[dict[str, Any]], float | int | str | None]
    available_fn: Callable[[dict[str, Any]], bool] = lambda data: True


ACCOUNT_SENSORS: tuple[RailwaySensorEntityDescription, ...] = (
    RailwaySensorEntityDescription(
        key="credit_balance",
        translation_key="credit_balance",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("customer", {}).get("creditBalance"),
        available_fn=lambda data: "customer" in data and data["customer"],
    ),
    RailwaySensorEntityDescription(
        key="current_usage",
        translation_key="current_usage",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("usage", {}).get("currentUsage"),
        available_fn=lambda data: "usage" in data and data["usage"],
    ),
    RailwaySensorEntityDescription(
        key="estimated_usage",
        translation_key="estimated_usage",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("usage", {}).get("estimatedUsage"),
        available_fn=lambda data: "usage" in data and data["usage"],
    ),
    RailwaySensorEntityDescription(
        key="projects_count",
        translation_key="projects_count",
        icon="mdi:folder-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("projects", [])),
    ),
    RailwaySensorEntityDescription(
        key="teams_count",
        translation_key="teams_count",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("teams", [])),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RailwayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Railway sensor based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[RailwaySensorEntity] = []

    # Add account-level sensors
    for description in ACCOUNT_SENSORS:
        entities.append(
            RailwaySensorEntity(
                coordinator=coordinator,
                description=description,
                entry=entry,
            )
        )

    # Add per-project sensors
    if coordinator.data:
        for project in coordinator.data.get("projects", []):
            project_id = project.get("id")
            project_name = project.get("name", "Unknown")

            if project_id:
                entities.append(
                    RailwayProjectUsageSensor(
                        coordinator=coordinator,
                        entry=entry,
                        project_id=project_id,
                        project_name=project_name,
                    )
                )

    async_add_entities(entities)


class RailwaySensorEntity(CoordinatorEntity[RailwayDataUpdateCoordinator], SensorEntity):
    """Representation of a Railway sensor."""

    entity_description: RailwaySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RailwayDataUpdateCoordinator,
        description: RailwaySensorEntityDescription,
        entry: RailwayConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data['account_id']}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["account_id"])},
            name=f"Railway ({entry.data.get('account_name', 'Account')})",
            manufacturer="Railway",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://railway.com",
        )

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available or not self.coordinator.data:
            return False
        return self.entity_description.available_fn(self.coordinator.data)


class RailwayProjectUsageSensor(
    CoordinatorEntity[RailwayDataUpdateCoordinator], SensorEntity
):
    """Sensor for individual project usage."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2
    _attr_translation_key = "project_usage"

    def __init__(
        self,
        coordinator: RailwayDataUpdateCoordinator,
        entry: RailwayConfigEntry,
        project_id: str,
        project_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._project_id = project_id
        self._project_name = project_name
        self._attr_unique_id = f"{entry.data['account_id']}_project_{project_id}_usage"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"project_{project_id}")},
            name=f"Railway Project: {project_name}",
            manufacturer="Railway",
            entry_type=DeviceEntryType.SERVICE,
            via_device=(DOMAIN, entry.data["account_id"]),
        )
        self._attr_translation_placeholders = {"project_name": project_name}

    @property
    def native_value(self) -> float | None:
        """Return the project usage."""
        if not self.coordinator.data:
            return None

        project_usage = self.coordinator.data.get("project_usage", {})
        usage = project_usage.get(self._project_id, {})
        return usage.get("currentUsage") or usage.get("estimatedUsage")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        project_usage = self.coordinator.data.get("project_usage", {})
        usage = project_usage.get(self._project_id, {})

        # Find project details
        projects = self.coordinator.data.get("projects", [])
        project = next((p for p in projects if p.get("id") == self._project_id), {})

        attrs = {
            "project_id": self._project_id,
            "project_name": self._project_name,
        }

        if usage.get("currentUsage") is not None:
            attrs["current_usage"] = usage["currentUsage"]
        if usage.get("estimatedUsage") is not None:
            attrs["estimated_usage"] = usage["estimatedUsage"]
        if project.get("description"):
            attrs["description"] = project["description"]
        if project.get("createdAt"):
            attrs["created_at"] = project["createdAt"]

        # Count services and environments
        services = project.get("services", {}).get("edges", [])
        environments = project.get("environments", {}).get("edges", [])
        attrs["services_count"] = len(services)
        attrs["environments_count"] = len(environments)

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available or not self.coordinator.data:
            return False
        return self._project_id in self.coordinator.data.get("project_usage", {})
