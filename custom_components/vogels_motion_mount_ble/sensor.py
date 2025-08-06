"""Sensor entities to define properties for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
            DistanceSensor(coordinator), RotationSensor(coordinator),
            CEBBLSensor(coordinator),
            MCPHWSensor(coordinator), MCPBLSensor(coordinator), MCPFWSensor(coordinator)
        ]

    # Create the sensors.
    async_add_entities(sensors)


class DistanceSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current distance, may be different from requested distance."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "Distance"
        self._attr_unique_id = "current_distance"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = "%"
        super().__init__(coordinator)

    @property
    def native_value(self):
        """Sensor for Rotation."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.distance

class RotationSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current rotation, may be different from requested rotation."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "Rotation"
        self._attr_unique_id = "current_rotation"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = "%"
        super().__init__(coordinator)

    @property
    def native_value(self):
        """Return the state of the roration or None."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.rotation

class CEBBLSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for CEB BL Version."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "CEB BL Version"
        self._attr_unique_id = "ceb_bl_version"
        self._attr_device_class = None
        super().__init__(coordinator)

    @property
    def native_value(self):
        """Return the state of ceb fwbl version or None."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.ceb_bl_version

class MCPHWSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP HW Version."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "MCP HW Version"
        self._attr_unique_id = "mcp_hw_version"
        self._attr_device_class = None
        super().__init__(coordinator)

    @property
    def native_value(self):
        """Return the state of ceb fw version or None."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.mcp_hw_version

class MCPBLSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP BL Version."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "MCP BL Version"
        self._attr_unique_id = "mcp_bl_version"
        self._attr_device_class = None
        super().__init__(coordinator)

    @property
    def native_value(self):
        """Return the state of mcp bl version or None."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.mcp_bl_version

class MCPFWSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP FW Version."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "MCP FW Version"
        self._attr_unique_id = "mcp_fw_version"
        self._attr_device_class = None
        super().__init__(coordinator)

    @property
    def native_value(self):
        """Return the state of mcp fw version or None."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.mcp_fw_version
