"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

from custom_components.vogels_motion_mount_ble.api import (
    SettingsRequestType,
    VogelsMotionMountActionType,
)

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator
from homeassistant.const import EntityCategory


async def async_setup_entry(
    _: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the TextEntities for name, preset names and pins."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            NameText(coordinator),
            *[PresetNameText(coordinator, preset_index) for preset_index in range(7)],
        ]
    )


class NameText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    _attr_unique_id = "name"
    _attr_translation_key = _attr_unique_id
    _attr_native_min = 1
    _attr_native_max = 20
    _attr_icon = "mdi:rename-box-outline"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self.coordinator.data.name

    @property
    def available(self) -> bool:
        """Set availability if user has permission."""
        return self.coordinator.api.has_permission(
            action_type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_name,
        )

    async def async_set_value(self, value: str) -> None:
        """Set the name value from the UI."""
        await self.coordinator.api.set_name(value)


class PresetNameText(VogelsMotionMountBlePresetBaseEntity, TextEntity):
    """Implementation of a sensor."""

    _attr_translation_key = "preset_name_custom"
    _attr_native_min = 1
    _attr_native_max = 32
    _attr_icon = "mdi:form-textbox"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_name_{self._prop_preset_index}"

    @property
    def available(self) -> bool:
        """Set availability if preset exists and user has permission."""
        return super().available and self.coordinator.api.has_permission(
            action_type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_presets,
        )

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.name
        return None

    async def async_set_value(self, value: str) -> None:
        """Set the preset name value from the UI."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index,
            name=value,
        )
