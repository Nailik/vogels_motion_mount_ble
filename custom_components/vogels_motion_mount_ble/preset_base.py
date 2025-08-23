"""Base entity to define common properties and methods for Vogels Motion Mount BLE Preset entities."""

import logging

from .api import VogelsMotionMountPreset
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBlePresetBaseEntity(VogelsMotionMountBleBaseEntity):
    """Base Entity Class For Preset Entities."""

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

    @property
    def available(self) -> bool:
        """Set availability of this index of Preset entity based on the lengths of presets in the data."""
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
