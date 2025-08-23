"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_NAME_ID,
    HA_SERVICE_PRESET_ID,
    HA_SERVICE_SET_NAME,
    HA_SERVICE_SET_PRESET_NAME,
)
from .coordinator import VogelsMotionMountBleCoordinator
from .preset_base import VogelsMotionMountBlePresetBaseEntity
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _set_name(call: ServiceCall) -> None:
    _LOGGER.debug("_set_name called with data: %s", call.data)
    await get_coordinator(call).api.set_name(call.data[HA_SERVICE_NAME_ID])


async def _set_preset_name(call: ServiceCall) -> None:
    _LOGGER.debug("_set_name called with data: %s", call.data)
    await get_coordinator(call).api.set_preset(
        preset_index=call.data[HA_SERVICE_NAME_ID], name=call.data[HA_SERVICE_PRESET_ID]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the TextEntities for name and preset names."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_NAME,
        _set_name,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_PRESET_NAME,
        _set_preset_name,
    )

    async_add_entities(
        [NameText(coordinator)]
        + [PresetNameText(coordinator, preset_index) for preset_index in range(7)]
    )


class NameText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    _attr_unique_id = "name"
    _attr_translation_key = _attr_unique_id
    _attr_native_min = 1
    _attr_native_max = 20

    @property
    def native_value(self):
        """Return the state of the entity."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.name

    async def async_set_value(self, value: str) -> None:
        """Set the name value from the UI."""
        await self.coordinator.api.set_name(value)


class PresetNameText(VogelsMotionMountBlePresetBaseEntity, TextEntity):
    """Implementation of a sensor."""

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_{preset_index}_name"
        self._attr_translation_key = "preset_name_custom"
        self._attr_native_min = 1
        self._attr_native_max = 20  # TODO correct max length?

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.name
        return None

    async def async_set_value(self, value: str) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index, name=value
        )
