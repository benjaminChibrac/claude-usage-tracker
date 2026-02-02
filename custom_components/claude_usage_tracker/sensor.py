"""Sensor platform for Claude Usage integration."""
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClaudeUsageDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Claude Usage sensors from a config entry."""
    coordinator: ClaudeUsageDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        ClaudeSessionUsedSensor(coordinator),
        ClaudeSessionLimitSensor(coordinator),
        ClaudeSessionPercentageSensor(coordinator),
        ClaudeSessionRemainingSensor(coordinator),
        ClaudeSessionActiveSensor(coordinator),
        ClaudeSessionBurnRateSensor(coordinator),
        ClaudeWeeklyUsedSensor(coordinator),
        ClaudeWeeklyLimitSensor(coordinator),
        ClaudeWeeklyPercentageSensor(coordinator),
        ClaudeWeeklyRemainingSensor(coordinator),
    ]

    async_add_entities(sensors)


class ClaudeUsageSensorBase(CoordinatorEntity[ClaudeUsageDataUpdateCoordinator], SensorEntity):
    """Base class for Claude Usage sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ClaudeUsageDataUpdateCoordinator,
        sensor_type: str,
        name: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"


class ClaudeSessionUsedSensor(ClaudeUsageSensorBase):
    """Sensor for session usage amount."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "session_used", "Session Used")
        self._attr_native_unit_of_measurement = "USD"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "session" in self.coordinator.data:
            return self.coordinator.data["session"].get("cost_usd")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "session" in self.coordinator.data:
            session = self.coordinator.data["session"]
            return {
                "started_at": session.get("started_at"),
                "ends_at": session.get("ends_at"),
                "projection_total_cost": session.get("projection", {}).get(
                    "total_cost"
                ),
            }
        return {}


class ClaudeSessionLimitSensor(ClaudeUsageSensorBase):
    """Sensor for session limit."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "session_limit", "Session Limit")
        self._attr_native_unit_of_measurement = "USD"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "session" in self.coordinator.data:
            return self.coordinator.data["session"].get("limit_usd")
        return None


class ClaudeSessionPercentageSensor(ClaudeUsageSensorBase):
    """Sensor for session usage percentage."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "session_percentage", "Session Usage")
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:percent"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "session" in self.coordinator.data:
            return self.coordinator.data["session"].get("percentage_used")
        return None


class ClaudeSessionRemainingSensor(ClaudeUsageSensorBase):
    """Sensor for session remaining budget."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "session_remaining", "Session Remaining")
        self._attr_native_unit_of_measurement = "USD"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:cash-minus"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "session" in self.coordinator.data:
            session = self.coordinator.data["session"]
            cost = session.get("cost_usd", 0)
            limit = session.get("limit_usd", 0)
            if cost is not None and limit is not None:
                return max(0, limit - cost)
        return None


class ClaudeSessionActiveSensor(ClaudeUsageSensorBase):
    """Binary sensor for session active status."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "session_active", "Session Active")
        self._attr_icon = "mdi:lightning-bolt"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "session" in self.coordinator.data:
            is_active = self.coordinator.data["session"].get("is_active", False)
            return "active" if is_active else "inactive"
        return "unknown"


class ClaudeSessionBurnRateSensor(ClaudeUsageSensorBase):
    """Sensor for session burn rate."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "session_burn_rate", "Session Burn Rate")
        self._attr_native_unit_of_measurement = "USD/h"
        self._attr_icon = "mdi:fire"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "session" in self.coordinator.data:
            projection = self.coordinator.data["session"].get("projection", {})
            return projection.get("burn_rate_per_hour")
        return None


class ClaudeWeeklyUsedSensor(ClaudeUsageSensorBase):
    """Sensor for weekly usage amount."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "weekly_used", "Weekly Used")
        self._attr_native_unit_of_measurement = "USD"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "weekly" in self.coordinator.data:
            return self.coordinator.data["weekly"].get("total_cost_usd")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data and "weekly" in self.coordinator.data:
            weekly = self.coordinator.data["weekly"]
            return {
                "week_start": weekly.get("week_start"),
            }
        return {}


class ClaudeWeeklyLimitSensor(ClaudeUsageSensorBase):
    """Sensor for weekly limit."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "weekly_limit", "Weekly Limit")
        self._attr_native_unit_of_measurement = "USD"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "weekly" in self.coordinator.data:
            return self.coordinator.data["weekly"].get("limit_usd")
        return None


class ClaudeWeeklyPercentageSensor(ClaudeUsageSensorBase):
    """Sensor for weekly usage percentage."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "weekly_percentage", "Weekly Usage")
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:percent"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "weekly" in self.coordinator.data:
            return self.coordinator.data["weekly"].get("percentage_used")
        return None


class ClaudeWeeklyRemainingSensor(ClaudeUsageSensorBase):
    """Sensor for weekly remaining budget."""

    def __init__(self, coordinator: ClaudeUsageDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "weekly_remaining", "Weekly Remaining")
        self._attr_native_unit_of_measurement = "USD"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:cash-minus"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "weekly" in self.coordinator.data:
            weekly = self.coordinator.data["weekly"]
            cost = weekly.get("total_cost_usd", 0)
            limit = weekly.get("limit_usd", 0)
            if cost is not None and limit is not None:
                return max(0, limit - cost)
        return None
