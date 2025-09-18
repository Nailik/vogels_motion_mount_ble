"""Button entities to define actions for Vogels Motion Mount BLE entities."""

from custom_components.vogels_motion_mount_ble.api import (
    SettingsRequestType,
    VogelsMotionMountActionType,
)
from propcache.api import cached_property

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .coordinator import VogelsMotionMountBleCoordinator


async def async_setup_entry(
    _: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the RefreshData and SelectPreset buttons."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            StartCalibratonButton(coordinator),
            RefreshDataButton(coordinator),
            DisconnectButton(coordinator),
            SelectPresetDefaultButton(coordinator),
            *[AddPresetButton(coordinator, preset_index) for preset_index in range(7)],
            *[
                DeletePresetButton(coordinator, preset_index)
                for preset_index in range(7)
            ],
            *[
                SelectPresetButton(coordinator, preset_index)
                for preset_index in range(7)
            ],
        ]
    )


class StartCalibratonButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to start the calibration."""

    _attr_unique_id = "start_calibration"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:rotate-3d"

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Set availability if user has permission."""
        return self.coordinator.api.has_permission(
            action_type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.start_calibration,
        )

    async def async_press(self):
        """Execute start calibration."""
        await self.coordinator.api.start_calibration()


class RefreshDataButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to refresh data."""

    _attr_unique_id = "refresh_data"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:refresh"

    @cached_property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Per default always available."""
        return True

    async def async_press(self):
        """Execute data refresh."""
        await self.coordinator.api.refresh_data()


class DisconnectButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to disconnect data."""

    _attr_unique_id = "disconnect"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:power-plug-off"

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Set availability only if device is connected currently."""
        if self.coordinator.data and self.coordinator.data.connected:
            return True
        return False

    async def async_press(self):
        """Execute disconnect."""
        await self.coordinator.api.disconnect()


class SelectPresetDefaultButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Buttons to select the default preset."""

    _attr_unique_id = "select_preset_default"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:wall"

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Set availability if user has permission."""
        return self.coordinator.api.has_permission(
            action_type=VogelsMotionMountActionType.Control,
        )

    async def async_press(self):
        """Select the default preset with id 0."""
        await self.coordinator.api.select_default_preset()


class SelectPresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to select the custom presets."""

    _attr_translation_key = "select_preset_custom"
    _attr_icon = "mdi:rotate-3d"

    def __init__(
        self,
        coordinator: VogelsMotionMountBleCoordinator,
        preset_index: int,
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(
            coordinator=coordinator,
            preset_index=preset_index,
        )
        self._attr_unique_id = f"select_preset_id_{preset_index}"

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Set availability if preset exists and user has permission."""
        return super().available and self.coordinator.api.has_permission(
            action_type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_presets,
        )

    async def async_press(self):
        """Select a custom preset by it's index."""
        await self.coordinator.api.select_preset(self._preset_index)


class DeletePresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to delete the custom presets."""

    _attr_translation_key = "delete_preset_custom"
    _attr_icon = "mdi:delete"

    def __init__(
        self,
        coordinator: VogelsMotionMountBleCoordinator,
        preset_index: int,
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"delete_preset_{self._prop_preset_index}"

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Set availability if preset exists and user has permission."""
        return super().available and self.coordinator.api.has_permission(
            action_type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_presets,
        )

    async def async_press(self):
        """Delete a custom preset by it's index."""
        await self.coordinator.api.delete_preset(self._preset_index)


class AddPresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to add the custom presets."""

    _attr_translation_key = "add_preset_custom"
    _attr_icon = "mdi:plus"

    def __init__(
        self,
        coordinator: VogelsMotionMountBleCoordinator,
        preset_index: int,
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"add_preset_{self._prop_preset_index}"

    async def async_press(self):
        """Add a custom preset by it's index with empty data."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index,
            name=f"{self._preset_index}",
            distance=0,
            rotation=0,
        )

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Set availability of this index of Preset entity based on the lengths of presets in the data."""
        if (
            self.coordinator.data
            and self.coordinator.data.presets
            and not self._preset
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
                settings_request_type=SettingsRequestType.change_presets,
            )
        ):
            return True
        return False
