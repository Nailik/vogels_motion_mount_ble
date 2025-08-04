"""Select entities to define properties for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator
from .const import CHAR_AUTOMOVE_ON_OPTIONS

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
    sensors = [AutomoveSelect(coordinator)]

    # Create the sensors.
    async_add_entities(sensors)


class AutomoveSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Implementation of a sensor."""

    _attr_options = ["off", "on 1", "on 2", "on 3", "on 4"]
    _attr_name = "Auto Move"
    _attr_unique_id = "auto_move"

    @property
    def current_option(self):
        """Return the state of the entity."""
        if not self.coordinator.data or not self.coordinator.data.automove_id:
            return None
        if self.coordinator.data.automove_on:
            return self._attr_options[self.coordinator.data.automove_id + 1]
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        index = self._attr_options.index(option)
        await self.coordinator.api.set_auto_move(index - 1 if (index != 0) else None)
