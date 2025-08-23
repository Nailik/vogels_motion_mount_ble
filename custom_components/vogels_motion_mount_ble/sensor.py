"""Sensor entities to define properties for Vogels Motion Mount BLE entities."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors for Distance, Rotation and versions."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    async_add_entities(
        [
            DistanceSensor(coordinator),
            RotationSensor(coordinator),
            CEBBLSensor(coordinator),
            MCPHWSensor(coordinator),
            MCPBLSensor(coordinator),
            MCPFWSensor(coordinator),
        ]
    )


class DistanceSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current distance, may be different from requested distance."""

    _attr_unique_id = "current_distance"
    _attr_translation_key = _attr_unique_id

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.distance


class RotationSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current rotation, may be different from requested rotation."""

    _attr_unique_id = "current_rotation"
    _attr_translation_key = _attr_unique_id

    @property
    def native_value(self):
        """Return the state of the roration or None."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.rotation


class CEBBLSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for CEB BL Version."""

    _attr_unique_id = "ceb_bl_version"
    _attr_translation_key = _attr_unique_id

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.ceb_bl_version


class MCPHWSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP HW Version."""

    _attr_unique_id = "mcp_hw_version"
    _attr_translation_key = _attr_unique_id

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.mcp_hw_version


class MCPBLSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP BL Version."""

    _attr_unique_id = "mcp_bl_version"
    _attr_translation_key = _attr_unique_id

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.mcp_bl_version


class MCPFWSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP FW Version."""

    _attr_unique_id = "mcp_fw_version"
    _attr_translation_key = _attr_unique_id

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.mcp_fw_version
