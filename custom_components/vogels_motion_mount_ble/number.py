"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .preset_base import VogelsMotionMountBlePresetBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_DEVICE_ID,
    HA_SERVICE_DISTANCE_ID,
    HA_SERVICE_ROTATION_ID,
    HA_SERVICE_SET_DISTANCE,
    HA_SERVICE_SET_ROTATION,
    HA_SERVICE_SET_TV_WIDTH,
    HA_SERVICE_TV_WIDTH_ID,
)
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)

async def _set_distance_service(call: ServiceCall) -> None:
    _LOGGER.debug("set_distance_service called with data: %s", call.data)
    device_registry = dr.async_get(call.hass)
    device = device_registry.async_get(call.data[HA_SERVICE_DEVICE_ID])
    entry_id = next(iter(device.config_entries))
    coordinator: VogelsMotionMountBleCoordinator = call.hass.data[DOMAIN].get(entry_id)

    await coordinator.api.set_distance(call.data[HA_SERVICE_DISTANCE_ID])

async def _set_rotation_service(call: ServiceCall) -> None:
    _LOGGER.debug("set_rotation_service called with data: %s", call.data)
    device_registry = dr.async_get(call.hass)
    device = device_registry.async_get(call.data[HA_SERVICE_DEVICE_ID])
    entry_id = next(iter(device.config_entries))
    coordinator: VogelsMotionMountBleCoordinator = call.hass.data[DOMAIN].get(entry_id)

    await coordinator.api.set_rotation(call.data[HA_SERVICE_ROTATION_ID])

async def _set_tv_width_service(call: ServiceCall) -> None:
    _LOGGER.debug("set_tv_width_service called with data: %s", call.data)
    device_registry = dr.async_get(call.hass)
    device = device_registry.async_get(call.data[HA_SERVICE_DEVICE_ID])
    entry_id = next(iter(device.config_entries))
    coordinator: VogelsMotionMountBleCoordinator = call.hass.data[DOMAIN].get(entry_id)

    await coordinator.api.set_width(call.data[HA_SERVICE_TV_WIDTH_ID])


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
        HA_SERVICE_SET_DISTANCE,
        _set_distance_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_ROTATION,
        _set_rotation_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_TV_WIDTH,
        _set_tv_width_service,
    )

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    numbers = [
        DistanceNumber(coordinator),
        RotationNumber(coordinator),
        TVWidthNumber(coordinator),
        *[PresetDistanceNumber(coordinator, preset_index) for preset_index in range(7)],
        *[PresetRotationNumber(coordinator, preset_index) for preset_index in range(7)],
    ]

    # Create the sensors.
    async_add_entities(numbers)

class DistanceNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """Implementation of a sensor."""

    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER
    _attr_min_value = 0
    _attr_max_value = 100
    _attr_step = 1

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
        if self.coordinator.data.requested_distance is not None:
            return self.coordinator.data.requested_distance
        return self.coordinator.data.distance

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_distance(value)

class RotationNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """Implementation of a sensor."""

    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -100
    _attr_native_max_value = 100
    _attr_native_step = 1

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
        if self.coordinator.data.requested_rotation is not None:
            return self.coordinator.data.requested_rotation
        return self.coordinator.data.rotation

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_rotation(value)


class TVWidthNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """Implementation of a number input for TV width."""

    _attr_native_unit_of_measurement = "cm"
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

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

class PresetDistanceNumber(VogelsMotionMountBlePresetBaseEntity, NumberEntity):
    """Implementation of a number input for distance of a preset."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int):
        """Initialise entity."""
        super().__init__(coordinator, preset_index)

    @property
    def name(self) -> str:
        """Return the name of the number entity."""
        return f"Preset {self._preset_name} Distance"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"preset_{self._preset_index}_distance"

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.distance
        return None

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(preset_id = self._preset_index, distance = value)

class PresetRotationNumber(VogelsMotionMountBlePresetBaseEntity, NumberEntity):
    """Implementation of a number input for distance of a preset."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int):
        """Initialise entity."""
        super().__init__(coordinator, preset_index)

    @property
    def name(self) -> str:
        """Return the name of the number entity."""
        return f"Preset {self._preset_name} Rotation"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"preset_{self._preset_index}_rotation"

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.rotation
        return None

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(preset_id = self._preset_index, rotation = value)

