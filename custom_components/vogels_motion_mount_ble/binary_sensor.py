"""Binary sensor entities to define properties for Vogels Motion Mount BLE entities."""

from functools import cached_property
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up the connection Sensors."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data
    async_add_entities([ConnectionBinarySensor(coordinator)])


class ConnectionBinarySensor(VogelsMotionMountBleBaseEntity, BinarySensorEntity):
    """Sensor to indicate if the Vogels Motion Mount is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_unique_id = "connection"
    _attr_translation_key = _attr_unique_id

    @cached_property
    def available(self) -> bool:  # type: ignore
        """Set availability if preset exists and user has permission."""
        return True

    @property
    def is_on(self):  # type: ignore
        """Return if the MotionMount is currently connected."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.connected

    @property
    def icon(self):  # type: ignore
        """Return icon."""
        return "mdi:wifi" if self.is_on else "mdi:wifi-off"
