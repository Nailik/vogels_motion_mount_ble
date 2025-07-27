"""Interfaces with the Integration 101 Template api sensors."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyConfigEntry
from .base import ExampleBaseEntity
from .const import DOMAIN
from .coordinator import ExampleCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: ExampleCoordinator = config_entry.runtime_data.coordinator

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [DistanceSensor(coordinator),RotationSensor(coordinator)]

    # Create the sensors.
    async_add_entities(sensors)


class DistanceSensor(ExampleBaseEntity, SensorEntity):
    """Implementation of a sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "distance"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.coordinator.mac}-distance"

    @property
    def native_value(self) -> int:
        """Return the state of the entity."""
        _LOGGER.exception("native_value DistanceSensor")
        if not self.coordinator.data:
            _LOGGER.error("No data available in coordinator")
            return None
        # This needs to enumerate to true or false
        return self.coordinator.data.distance

class RotationSensor(ExampleBaseEntity, SensorEntity):
    """Implementation of a sensor."""

    _attr_device_class = None
    _attr_native_unit_of_measurement = "°"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "rotation"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.coordinator.mac}-rotation"

    @property
    def native_value(self) -> int:
        """Return the state of the entity."""
        _LOGGER.exception("native_value RotationSensor")
        if not self.coordinator.data:
            _LOGGER.error("No data available in coordinator")
            return None
        # This needs to enumerate to true or false
        return self.coordinator.data.rotation
