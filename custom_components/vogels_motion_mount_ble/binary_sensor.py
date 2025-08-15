"""Binary sensor entities to define properties for Vogels Motion Mount BLE entities."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the connection Sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ConnectionBinarySensor(coordinator)])


class ConnectionBinarySensor(VogelsMotionMountBleBaseEntity, BinarySensorEntity):
    """Sensor to indicate if the Vogels Motion Mount is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_unique_id = "connection"
    _attr_translation_key = _attr_unique_id

    @property
    def is_on(self):
        """Return if the MotionMount is currently connected."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.connected
