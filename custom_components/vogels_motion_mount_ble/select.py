"""Select entities to define properties for Vogels Motion Mount BLE entities."""

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .api import VogelsMotionMountAutoMoveType
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Selectors for automove."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    async_add_entities([AutomoveSelect(coordinator), FreezePresetSelect(coordinator)])


class AutomoveSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Implementation of the Automove Selector."""

    _attr_unique_id = "auto_move"
    _attr_translation_key = _attr_unique_id
    _attr_options = ["off", "hdmi_1", "hdmi_2", "hdmi_3", "hdmi_4", "hdmi_5"]
    _attr_icon = "mdi:autorenew"

    @property
    def current_option(self):
        """Return the current active automove option."""
        if self.coordinator.data is None or self.coordinator.data.automove_type is None:
            return None
        return self.coordinator.data.automove_type.value

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        await self.coordinator.api.set_automove(option)


class FreezePresetSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Implementation of the Freeze preset Selector."""

    _attr_unique_id = "freeze_preset"
    _attr_translation_key = _attr_unique_id
    _attr_options = ["0", "1", "2", "3", "4", "5", "6", "7"]
    _attr_icon = "mdi:snowflake"

    @property
    def current_option(self):
        """Return the current selected freeze preset."""
        if self.coordinator.data is None:
            return None
        if self.coordinator.data.freeze_preset_index is None:
            return None
        return self._attr_options[self.coordinator.data.freeze_preset_index]

    @property
    def available(self) -> bool:
        """Set availability if automove is turned on."""
        if (
            self.coordinator.data
            and self.coordinator.data.automove_type
            is not VogelsMotionMountAutoMoveType.Off
        ):
            return True
        return False

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        index = self._attr_options.index(option)
        await self.coordinator.api.set_freeze_preset(index)
