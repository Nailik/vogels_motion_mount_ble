"""Base entity to define common properties and methods for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .base import VogelsMotionMountBleBaseEntity
from .api import VogelsMotionMountPreset
from .const import DOMAIN
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBlePresetBaseEntity(VogelsMotionMountBleBaseEntity):
    """Base Entity Class For Preset Entities.

    This inherits a CoordinatorEntity class to register your entites to be updated
    by your DataUpdateCoordinator when async_update_data is called, either on the scheduled
    interval or by forcing an update.
    """

    # True causes HA to name your entities with the device name and entity name.
    _attr_has_entity_name = True

    def __init__(self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int) -> None:
        """Initialise entity."""
        super().__init__(coordinator)
        self._preset_index = preset_index

    @property
    def _preset_name(self) -> str:
        """Return the name of the preset or it's index."""
        if self._preset:
            return f"{self._preset.name}"
        return f"{self._preset_index}"

    @property
    def _preset(self) -> VogelsMotionMountPreset | None:
        """Return the name of the preset or it's index."""
        if self.coordinator.data and self.coordinator.data.presets and self._preset_index in self.coordinator.data.presets:
            return self.coordinator.data.presets[self._preset_index]
        return None
