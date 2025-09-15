"""Base entity to define common properties and methods for Vogels Motion Mount BLE entities."""

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import VogelsMotionMountPreset
from .const import DOMAIN
from .coordinator import VogelsMotionMountBleCoordinator


class VogelsMotionMountBleBaseEntity(CoordinatorEntity):
    """Base Entity Class for all Entities."""

    coordinator: VogelsMotionMountBleCoordinator
    _attr_has_entity_name: bool = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self.coordinator.name,
            manufacturer="Vogel's",
            model="Motion Mount",
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()


class VogelsMotionMountBlePresetBaseEntity(VogelsMotionMountBleBaseEntity):
    """Base Entity Class For Preset Entities."""

    def __init__(
        self,
        coordinator: VogelsMotionMountBleCoordinator,
        preset_index: int,
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator=coordinator)
        self._preset_index = preset_index
        self._attr_translation_placeholders = {"preset": self._prop_preset_index}

    @property
    def available(self) -> bool:
        """Set availability of this index of Preset entity based if the preset is available in the data."""
        return self._preset is not None

    @property
    def _prop_preset_index(self) -> str:
        """Index of the preset."""
        # Note: seems to be required to use _preset, when using _preset_index it is not correctly working and will change it's entity id when recreating entities
        if self._preset:
            return f"{self._preset.index}"
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
