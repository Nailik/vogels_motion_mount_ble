"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator
from homeassistant.components.number import NumberEntity, NumberMode

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
    sensors = [TVWidthNumber(coordinator)]

    # Create the sensors.
    async_add_entities(sensors)

class TVWidthNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """Implementation of a number input for TV width."""

    _attr_native_unit_of_measurement = "cm"
    _attr_mode = NumberMode.BOX
    _attr_step = 1

    @property
    def name(self) -> str:
        """Return the name of the number entity."""
        return "tvwidth"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return "tv_width"

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.width

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_width(value)
