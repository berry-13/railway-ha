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


def get_total_credit_balance(data: dict[str, Any]) -> float | None:
    """Get total credit balance across all workspaces."""
    workspaces = data.get("workspaces", [])
    if not workspaces:
        return None
    total = 0.0
    has_data = False
    for ws in workspaces:
        customer = ws.get("customer", {})
        if customer and customer.get("creditBalance") is not None:
            total += customer["creditBalance"]
            has_data = True
    return total if has_data else None


def get_total_current_usage(data: dict[str, Any]) -> float | None:
    """Get total current usage across all workspaces."""
    workspaces = data.get("workspaces", [])
    if not workspaces:
        return None
    total = 0.0
    has_data = False
    for ws in workspaces:
        customer = ws.get("customer", {})
        if customer and customer.get("currentUsage") is not None:
            total += customer["currentUsage"]
            has_data = True
    return total if has_data else None


def get_remaining_credits(data: dict[str, Any]) -> float | None:
    """Get remaining usage credit balance across all workspaces."""
    workspaces = data.get("workspaces", [])
    if not workspaces:
        return None
    total = 0.0
    has_data = False
    for ws in workspaces:
        customer = ws.get("customer", {})
        if customer and customer.get("remainingUsageCreditBalance") is not None:
            total += customer["remainingUsageCreditBalance"]
            has_data = True
    return total if has_data else None


def get_earnings_value(key: str):
    """Create a function to get an earnings value by key."""

    def getter(data: dict[str, Any]) -> float | int | None:
        earnings = data.get("earnings", {})
        return earnings.get(key)

    return getter


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
        value_fn=get_total_credit_balance,
        available_fn=lambda data: bool(data.get("workspaces")),
    ),
    RailwaySensorEntityDescription(
        key="current_usage",
        translation_key="current_usage",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=get_total_current_usage,
        available_fn=lambda data: bool(data.get("workspaces")),
    ),
    RailwaySensorEntityDescription(
        key="remaining_credits",
        translation_key="remaining_credits",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=get_remaining_credits,
        available_fn=lambda data: bool(data.get("workspaces")),
    ),
    RailwaySensorEntityDescription(
        key="projects_count",
        translation_key="projects_count",
        icon="mdi:folder-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("projects", [])),
    ),
    RailwaySensorEntityDescription(
        key="workspaces_count",
        translation_key="workspaces_count",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("workspaces", [])),
    ),
    RailwaySensorEntityDescription(
        key="templates_earnings_30d",
        translation_key="templates_earnings_30d",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:file-document-multiple",
        value_fn=get_earnings_value("templates_30d"),
        available_fn=lambda data: bool(data.get("templates")),
    ),
    RailwaySensorEntityDescription(
        key="templates_total_earnings",
        translation_key="templates_total_earnings",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:file-document-multiple-outline",
        value_fn=get_earnings_value("templates_total"),
        available_fn=lambda data: bool(data.get("templates")),
    ),
    RailwaySensorEntityDescription(
        key="referrals_credited",
        translation_key="referrals_credited",
        icon="mdi:account-arrow-right",
        state_class=SensorStateClass.TOTAL,
        value_fn=get_earnings_value("referrals_credited"),
        available_fn=lambda data: bool(data.get("referrals")),
    ),
    RailwaySensorEntityDescription(
        key="referrals_pending",
        translation_key="referrals_pending",
        icon="mdi:account-clock",
        state_class=SensorStateClass.TOTAL,
        value_fn=get_earnings_value("referrals_pending"),
        available_fn=lambda data: bool(data.get("referrals")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RailwayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Railway sensor based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    # Add account-level sensors
    for description in ACCOUNT_SENSORS:
        entities.append(
            RailwaySensorEntity(
                coordinator=coordinator,
                description=description,
                entry=entry,
            )
        )

    # Add per-workspace sensors
    if coordinator.data:
        for workspace in coordinator.data.get("workspaces", []):
            ws_id = workspace.get("id")
            ws_name = workspace.get("name", "Unknown")

            if ws_id:
                entities.append(
                    RailwayWorkspaceSensor(
                        coordinator=coordinator,
                        entry=entry,
                        workspace_id=ws_id,
                        workspace_name=ws_name,
                    )
                )

    async_add_entities(entities)


class RailwaySensorEntity(
    CoordinatorEntity[RailwayDataUpdateCoordinator], SensorEntity
):
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


class RailwayWorkspaceSensor(
    CoordinatorEntity[RailwayDataUpdateCoordinator], SensorEntity
):
    """Sensor for individual workspace billing."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2
    _attr_translation_key = "workspace_usage"

    def __init__(
        self,
        coordinator: RailwayDataUpdateCoordinator,
        entry: RailwayConfigEntry,
        workspace_id: str,
        workspace_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._workspace_id = workspace_id
        self._workspace_name = workspace_name
        self._attr_unique_id = (
            f"{entry.data['account_id']}_workspace_{workspace_id}_usage"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"workspace_{workspace_id}")},
            name=f"Railway Workspace: {workspace_name}",
            manufacturer="Railway",
            entry_type=DeviceEntryType.SERVICE,
            via_device=(DOMAIN, entry.data["account_id"]),
        )
        self._attr_translation_placeholders = {"workspace_name": workspace_name}

    def _get_workspace(self) -> dict[str, Any] | None:
        """Get the workspace data."""
        if not self.coordinator.data:
            return None
        for ws in self.coordinator.data.get("workspaces", []):
            if ws.get("id") == self._workspace_id:
                return ws
        return None

    @property
    def native_value(self) -> float | None:
        """Return the workspace current usage."""
        workspace = self._get_workspace()
        if not workspace:
            return None
        customer = workspace.get("customer", {})
        return customer.get("currentUsage")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        workspace = self._get_workspace()
        if not workspace:
            return {}

        customer = workspace.get("customer", {})

        attrs: dict[str, Any] = {
            "workspace_id": self._workspace_id,
            "workspace_name": self._workspace_name,
        }

        if customer.get("creditBalance") is not None:
            attrs["credit_balance"] = customer["creditBalance"]
        if customer.get("currentUsage") is not None:
            attrs["current_usage"] = customer["currentUsage"]
        if customer.get("remainingUsageCreditBalance") is not None:
            attrs["remaining_credits"] = customer["remainingUsageCreditBalance"]
        if customer.get("appliedCredits") is not None:
            attrs["applied_credits"] = customer["appliedCredits"]
        if customer.get("billingEmail"):
            attrs["billing_email"] = customer["billingEmail"]
        if customer.get("state"):
            attrs["subscription_state"] = customer["state"]
        if customer.get("isTrialing") is not None:
            attrs["is_trialing"] = customer["isTrialing"]
        if customer.get("trialDaysRemaining") is not None:
            attrs["trial_days_remaining"] = customer["trialDaysRemaining"]

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available or not self.coordinator.data:
            return False
        return self._get_workspace() is not None
