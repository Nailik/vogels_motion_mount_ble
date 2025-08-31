"""Base entity to define common properties and methods for Vogels Motion Mount BLE entities."""

import logging
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import VogelsMotionMountPreset
from .const import DOMAIN
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)

class VogelsMotionMountBleBaseEntity(CoordinatorEntity):
    """Base Entity Class for all Entities."""

    coordinator: VogelsMotionMountBleCoordinator
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self.coordinator.name,
            manufacturer="Vogels",
            model="Motion Mount",
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()


class VogelsMotionMountBlePresetBaseEntity(VogelsMotionMountBleBaseEntity):
    """Base Entity Class For Preset Entities."""
    #TODO name doesn't update yet directly
    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator)
        self._preset_index = preset_index
        self._attr_translation_placeholders = {
            "name": self._preset_name,
            "index": self._preset_index,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self._attr_translation_placeholders = {
            "name": self._preset_name,
        }
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information."""
        if not self.coordinator.preset_subdevice:
            return super().device_info
        return DeviceInfo(
            name=f"Preset {self._preset_name}",
            manufacturer="Vogels",
            model="Motion Mount",
            identifiers={(DOMAIN, f"{self.coordinator.mac}_{self._preset_index}")},
            via_device=(DOMAIN, self.coordinator.mac),
        )

    @property
    def available(self) -> bool:
        """Set availability of this index of Preset entity based if the preset is available in the data."""
        return self._preset is not None

    @property
    def _preset_name(self) -> str:
        """Name of the preset or it's index if no name is available."""
        if self._preset:
            return f"{self._preset.name}"
        return f"{self._preset_index}"

    @property
    def _preset(self) -> VogelsMotionMountPreset | None:
        """Preset if available or none."""
        if (
            self.coordinator.data
            and self.coordinator.data.presets
            and self._preset_index in self.coordinator.data.presets
        ):
            return self.coordinator.data.presets[self._preset_index]
        return None
