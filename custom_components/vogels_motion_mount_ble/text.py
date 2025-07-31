"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .preset_base import VogelsMotionMountBlePresetBaseEntity

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import DOMAIN, HA_SERVICE_DEVICE_ID, HA_SERVICE_NAME_ID, HA_SERVICE_SET_NAME
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)

async def _set_name(call: ServiceCall) -> None:
    _LOGGER.debug("set_distance_service called with data: %s", call.data)
    device_registry = dr.async_get(call.hass)
    device = device_registry.async_get(call.data[HA_SERVICE_DEVICE_ID])
    entry_id = next(iter(device.config_entries))
    coordinator: VogelsMotionMountBleCoordinator = call.hass.data[DOMAIN].get(entry_id)

    await coordinator.api.set_name(call.data[HA_SERVICE_NAME_ID])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator


    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_NAME,
        _set_name,
    )

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    numbers = [NameText(coordinator)]  + [PresetNameText(coordinator, preset_index) for preset_index in range(7)]

    # Create the sensors.
    async_add_entities(numbers)

class NameText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a sensor."""

    _attr_native_min = 1
    _attr_native_max = 20

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "name"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return "name"

    @property
    def native_value(self):
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.name

    async def async_set_value(self, value: str) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_name(value)

class PresetNameText(VogelsMotionMountBlePresetBaseEntity, TextEntity):
    """Implementation of a sensor."""

    _attr_native_min = 1
    _attr_native_max = 20

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int):
        """Initialise entity."""
        super().__init__(coordinator, preset_index)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if self._preset:
            return  f"Preset {self._preset_name} Name"
        return  f"Preset {self._preset_index} Name"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"preset_{self._preset_index}_name"

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.name
        return None

    @property
    def extra_state_attributes(self):
        return {
            "friendly_name": f"Preset {self._preset_name} Name",  # updates UI name
        }

    async def async_native_set_value(self, value: str) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(preset_id = self._preset_index, name = value)
