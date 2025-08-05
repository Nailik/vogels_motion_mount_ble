"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import DOMAIN, HA_SERVICE_NAME_ID, HA_SERVICE_SET_NAME
from .coordinator import VogelsMotionMountBleCoordinator
from .preset_base import VogelsMotionMountBlePresetBaseEntity
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _set_name(call: ServiceCall) -> None:
    await get_coordinator(call).set_name(call.data[HA_SERVICE_NAME_ID])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator
    # register services
    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_NAME,
        _set_name,
    )

    # register entities
    async_add_entities(
        [NameText(coordinator)]
        + [PresetNameText(coordinator, preset_index) for preset_index in range(7)]
    )


class NameText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator) -> None:
        """Initialise entity."""
        self._attr_name = "Name"
        self._attr_unique_id = "name"
        self._attr_native_min = 1
        self._attr_native_max = 20
        super().__init__(coordinator)

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

    _attr_native_min = 1
    _attr_native_max = 20

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int):
        """Initialise entity."""
        super().__init__(coordinator, preset_index)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if self._preset:
            return f"Preset {self._preset_name} Name"
        return f"Preset {self._preset_index} Name"

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

    async def async_native_set_value(self, value: str) -> None:
        """Set the value from the UI."""
        await self.coordinator.api.set_preset(preset_id=self._preset_index, name=value)
