"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_DISTANCE_ID,
    HA_SERVICE_ROTATION_ID,
    HA_SERVICE_SET_DISTANCE,
    HA_SERVICE_SET_ROTATION,
    HA_SERVICE_SET_PRESET_DISTANCE,
    HA_SERVICE_SET_PRESET_ROTATION,
    HA_SERVICE_SET_TV_WIDTH,
    HA_SERVICE_TV_WIDTH_ID,
)
from .coordinator import VogelsMotionMountBleCoordinator
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _set_distance_service(call: ServiceCall) -> None:
    _LOGGER.debug("_set_distance_service called with data: %s", call.data)
    await get_coordinator(call).api.set_distance(call.data[HA_SERVICE_DISTANCE_ID])


async def _set_rotation_service(call: ServiceCall) -> None:
    _LOGGER.debug("_set_rotation_service called with data: %s", call.data)
    await get_coordinator(call).api.set_rotation(call.data[HA_SERVICE_ROTATION_ID])


async def _set_tv_width_service(call: ServiceCall) -> None:
    _LOGGER.debug("set_tv_width_service called with data: %s", call.data)
    await get_coordinator(call).api.set_width(call.data[HA_SERVICE_TV_WIDTH_ID])


async def _set_preset_distance_service(call: ServiceCall) -> None:
    _LOGGER.debug("_set_preset_distance_service called with data: %s", call.data)
    await get_coordinator(call).api.set_preset(
        preset_index=call.data[HA_SERVICE_SET_PRESET_DISTANCE],
        distance=call.data[HA_SERVICE_DISTANCE_ID],
    )


async def _set_preset_rotation_service(call: ServiceCall) -> None:
    _LOGGER.debug("_set_preset_rotation_service called with data: %s", call.data)
    await get_coordinator(call).api.set_preset(
        call.data[HA_SERVICE_SET_PRESET_ROTATION],
        rotation=call.data[HA_SERVICE_ROTATION_ID],
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Numbers for distance, rotation, tv width and preset (distance, rotation)."""
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

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_PRESET_DISTANCE,
        _set_preset_distance_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_PRESET_ROTATION,
        _set_preset_rotation_service,
    )

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    numbers = [
        DistanceNumber(coordinator),
        RotationNumber(coordinator),
        TVWidthNumber(coordinator),
        *[
            PresetDistanceNumber(coordinator, preset_index)
            for preset_index in range(1, 8)
        ],
        *[
            PresetRotationNumber(coordinator, preset_index)
            for preset_index in range(1, 8)
        ],
    ]

    # Create the sensors.
    async_add_entities(numbers)


class DistanceNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """Implementation of the NumberEntity to set the distance."""

    _attr_unique_id = "distance"
    _attr_translation_key = _attr_unique_id
    _attr_mode = NumberMode.SLIDER
    _attr_min_value = 0
    _attr_max_value = 100
    _attr_step = 1

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
    """Implementation of the NumberEntity to set the rotation."""

    _attr_unique_id = "rotation"
    _attr_translation_key = _attr_unique_id
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -100
    _attr_native_max_value = 100
    _attr_native_step = 1

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

    _attr_unique_id = "tv_width"
    _attr_translation_key = _attr_unique_id
    _attr_native_unit_of_measurement = "cm"
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

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

    _attr_mode = NumberMode.SLIDER
    _attr_min_value = 0
    _attr_max_value = 100
    _attr_step = 1

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_{preset_index}_distance"
        self._attr_translation_key = "preset_distance_custom"

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.distance
        return None

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index, distance=value
        )


class PresetRotationNumber(VogelsMotionMountBlePresetBaseEntity, NumberEntity):
    """Implementation of a number input for distance of a preset."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -100
    _attr_native_max_value = 100
    _attr_native_step = 1

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_{preset_index}_rotation"
        self._attr_translation_key = "preset_rotation_custom"

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.rotation
        return None

    async def async_set_native_value(self, value: int) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index, rotation=value
        )
