"""Select entities to define properties for Vogels Motion Mount BLE entities."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import DISTANCE_TOLERANCE, ROTATION_TOLERANCE
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
            CurrentPresetSelect(coordinator),
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
        return super().available and self.coordinator.data.permissions.change_tv_on_off_detection

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
        return super().available and self.coordinator.data.permissions.change_default_position

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        index = self.options.index(option)
        await self.coordinator.set_freeze_preset(index)


class CurrentPresetSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Selector that detects the current preset based on distance and rotation and allows to move to a preset."""

    _attr_unique_id = "current_preset"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:television-guide"

    @property
    def _preset_options(self) -> list[tuple[str, int, int, int]]:
        """Return (option, device preset index, distance, rotation) for default and all existing presets."""
        # default preset (wall position) has device index 0
        options = [("0", 0, 0, 0)]
        used = {"0"}
        for preset in self.coordinator.data.presets:
            if preset.data is None:
                continue
            option = str(preset.data.name)
            if option in used:
                # keep options unique if presets share the same name
                option = f"{option} ({preset.index + 1})"
            used.add(option)
            # custom presets are offset by 1 due to default preset
            options.append(
                (option, preset.index + 1, preset.data.distance, preset.data.rotation)
            )
        return options

    @property
    def options(self) -> list[str]:
        """Return the possible options."""
        return [option for option, _, _, _ in self._preset_options]

    @property
    def current_option(self) -> str | None:
        """Return the preset closest to the current position within the tolerance, None if there is none."""
        distance = self.coordinator.data.distance
        rotation = self.coordinator.data.rotation
        matches = [
            (abs(distance - preset_distance) + abs(rotation - preset_rotation), option)
            for option, _, preset_distance, preset_rotation in self._preset_options
            if abs(distance - preset_distance) <= DISTANCE_TOLERANCE
            and abs(rotation - preset_rotation) <= ROTATION_TOLERANCE
        ]
        if not matches:
            return None
        return min(matches, key=lambda match: match[0])[1]

    async def async_select_option(self, option: str) -> None:
        """Move to the selected preset."""
        index = next(
            index for name, index, _, _ in self._preset_options if name == option
        )
        await self.coordinator.select_preset(index)
