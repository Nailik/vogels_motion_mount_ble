"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the TextEntities for name, preset names and pins."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    async_add_entities(
        [
            NameText(coordinator),
        ]
        + [PresetNameText(coordinator, preset_index) for preset_index in range(7)]
    )


class NameText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    _attr_unique_id = "name"
    _attr_translation_key = _attr_unique_id
    _attr_native_min = 1
    _attr_native_max = 20
    _attr_icon = "mdi:rename-box-outline"

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

    _attr_translation_key = "preset_name_custom"
    _attr_native_min = 1
    _attr_native_max = 32
    _attr_icon = "mdi:form-textbox"

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_name_{self._prop_preset_index}"

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.name
        return None

    async def async_set_value(self, value: str) -> None:
        """Set the preset name value from the UI."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index, name=value
        )
