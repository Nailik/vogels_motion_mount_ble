"""Binary sensor entities to define properties for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Binary Sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ConnectionBinarySensor(coordinator)])


class ConnectionBinarySensor(VogelsMotionMountBleBaseEntity, BinarySensorEntity):
    """Sensor to indicate if the Vogels Motion Mount is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "connection"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-{self.coordinator.mac}-connected"

    @property
    def is_on(self):
        """Return if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.connected
