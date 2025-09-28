"""Select entities to define properties for Vogels Motion Mount BLE entities."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator
from .data import VogelsMotionMountAutoMoveType


async def async_setup_entry(
    _: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Selectors for automove."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            AutomoveSelect(coordinator),
            FreezePresetSelect(coordinator),
        ]
    )


class AutomoveSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Implementation of the Automove Selector."""

    _attr_unique_id = "auto_move"
    _attr_translation_key = _attr_unique_id
    _attr_options = ["0", "1", "2", "3", "4", "5"]
    _attr_icon = "mdi:autorenew"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        """Set availability if preset exists and user has permission."""
        return self.coordinator.data.permissions.change_tv_on_off_detection

    @property
    def current_option(self) -> str | None:
        """Return the current active automove option."""
        automove = self.coordinator.data.automove.value
        # Off → always "0"
        if automove % 2:
            return "0"
        # On → HDMI index = (value // 4) + 1
        return str((automove // 4) + 1)

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        current_value = self.coordinator.data.automove.value

        if option == "0":
            # Disabled → pick matching Off for current HDMI
            hdmi_index = (current_value // 4) + 1
            enum_value = (hdmi_index - 1) * 4 + 1
        else:
            # Enabled → On for selected HDMI
            hdmi_index = int(option)
            enum_value = (hdmi_index - 1) * 4

        target = VogelsMotionMountAutoMoveType(enum_value)
        await self.coordinator.set_automove(target)


class FreezePresetSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Implementation of the Freeze preset Selector."""

    _attr_unique_id = "freeze_preset"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:snowflake"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def current_option(self) -> str | None:
        """Return the current selected freeze preset."""
        index = self.coordinator.data.freeze_preset_index
        if index is None or not (0 <= index < len(self.options)):
            return None
        return self.options[index]

    @property
    def options(self) -> list[str]:
        """Return the possible options."""
        # Dynamically generated based on coordinator data
        return ["0"] + [
            str(preset.data.name)
            for preset in self.coordinator.data.presets
            if preset.data is not None
        ]

    @property
    def available(self) -> bool:
        """Set availability if automove is turned on."""
        return self.coordinator.data.permissions.change_default_position

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        index = self.options.index(option)
        await self.coordinator.set_freeze_preset(index)
