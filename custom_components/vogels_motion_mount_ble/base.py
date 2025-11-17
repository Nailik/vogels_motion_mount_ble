"""Base entity to define common properties and methods for Vogels Motion Mount BLE entities."""

from propcache.api import cached_property

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VogelsMotionMountBleCoordinator
from .data import VogelsMotionMountPreset


class VogelsMotionMountBleBaseEntity(
    CoordinatorEntity[VogelsMotionMountBleCoordinator]
):
    """Base Entity Class for all Entities."""

    _attr_has_entity_name: bool = True

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self.coordinator.name,
            manufacturer="Vogel's",
            model="Motion Mount",
            identifiers={(DOMAIN, self.coordinator.address)},
        )

    @property
    def available(self) -> bool:
        """Set availability of the entities only when the ble device is available."""
        return self.coordinator.last_update_success

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
        self._attr_translation_placeholders = {"preset": str(preset_index)}

    @property
    def available(self) -> bool:
        """Set availability of this index of Preset entity based if there is dat astored in the preset."""
        return super().available and self._preset.data is not None

    @property
    def _preset(self) -> VogelsMotionMountPreset:
        """Preset."""
        return self.coordinator.data.presets[self._preset_index]
