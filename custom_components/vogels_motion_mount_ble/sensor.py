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
    sensors = [DistanceSensor(coordinator), RotationSensor(coordinator), TVWidthSensor(coordinator)]

    # Create the sensors.
    async_add_entities(sensors)


class DistanceSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Implementation of a sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"  # TODO test this

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "distance"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return "distance"

    @property
    def native_value(self):
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.distance

class RotationSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Implementation of a sensor."""

    _attr_device_class = None  # TODO find a usefull class
    _attr_native_unit_of_measurement = "°"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "rotation"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return "rotation"

    @property
    def native_value(self):
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.rotation

class TVWidthSensor(VogelsMotionMountBleBaseEntity, SensorEntity):
    """Implementation of a sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "tvwidth"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return "tv_width"

    @property
    def native_value(self):
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.width
