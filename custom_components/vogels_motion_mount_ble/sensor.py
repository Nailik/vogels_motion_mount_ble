"""Sensor entities to define properties for Vogels Motion Mount BLE entities."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator


async def async_setup_entry(
    _: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors for Distance, Rotation, Pin and Versions."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            DistanceSensor(coordinator),
            RotationSensor(coordinator),
            CEBBLSensor(coordinator),
            MCPHWSensor(coordinator),
            MCPBLSensor(coordinator),
            MCPFWSensor(coordinator),
            PinSettingsSensor(coordinator),
            AuthenticationSensor(coordinator),
        ]
    )


class DistanceSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current distance, may be different from requested distance."""

    _attr_unique_id = "current_distance"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:ruler"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.distance


class RotationSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current rotation, may be different from requested rotation."""

    _attr_unique_id = "current_rotation"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:angle-obtuse"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        """Return the state of the rotation or None."""
        return self.coordinator.data.rotation


class CEBBLSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for CEB BL Version."""

    _attr_unique_id = "ceb_bl_version"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:alpha-v"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.versions.ceb_bl_version


class MCPHWSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP HW Version."""

    _attr_unique_id = "mcp_hw_version"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:alpha-v"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.versions.mcp_hw_version


class MCPBLSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP BL Version."""

    _attr_unique_id = "mcp_bl_version"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:alpha-v"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.versions.mcp_bl_version


class MCPFWSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for MCP FW Version."""

    _attr_unique_id = "mcp_fw_version"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:alpha-v"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.versions.mcp_fw_version


class PinSettingsSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for Pin Settings."""

    _attr_unique_id = "pin_settings"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:cloud-key"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.pin_setting.value


class AuthenticationSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Sensor for current Authentication level."""

    _attr_unique_id = "authentication"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:server-security"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.permissions.auth_status.auth_type.value
