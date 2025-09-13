"""Button entities to define actions for Vogels Motion Mount BLE entities."""

from homeassistant.components.button import ButtonEntity
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
    """Set up the RefreshData and SelectPreset buttons."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    async_add_entities(
        [
            RefreshDataButton(coordinator),
            DisconnectButton(coordinator),
            SelectPresetDefaultButton(coordinator),
        ]
        # Add one AddPresetButton for each preset_id from 0 to 7 inclusive
        + [AddPresetButton(coordinator, preset_index) for preset_index in range(7)]
        # Add one DeletePresetButton for each preset_id from 0 to 7 inclusive
        + [DeletePresetButton(coordinator, preset_index) for preset_index in range(7)]
        # Add one SelectPresetButton for each preset_id from 0 to 7 inclusive
        + [SelectPresetButton(coordinator, preset_index) for preset_index in range(7)]
    )


class RefreshDataButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to refresh data."""

    _attr_unique_id = "refresh_data"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:refresh"

    async def async_press(self):
        """Execute data refresh."""
        await self.coordinator.api.refresh_data()


class DisconnectButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to disconnect data."""

    _attr_unique_id = "disconnect"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:power-plug-off"

    @property
    def available(self) -> bool:
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

    async def async_press(self):
        """Select the default preset with id 0."""
        await self.coordinator.api.select_default_preset()


class SelectPresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to select the custom presets."""

    _attr_translation_key = "select_preset_custom"
    _attr_icon = "mdi:rotate-3d"

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"select_preset_id_{preset_index}"

    async def async_press(self):
        """Select a custom preset by it's index."""
        await self.coordinator.api.select_preset(self._preset_index)


class DeletePresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to delete the custom presets."""

    _attr_translation_key = "delete_preset_custom"
    _attr_icon = "mdi:delete"

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"delete_preset_{self._prop_preset_index}"

    async def async_press(self):
        """Delete a custom preset by it's index."""
        await self.coordinator.api.delete_preset(self._preset_index)


class AddPresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to add the custom presets."""

    _attr_translation_key = "add_preset_custom"
    _attr_icon = "mdi:plus"

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
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
    def available(self) -> bool:
        """Set availability of this index of Preset entity based on the lengths of presets in the data."""
        if self.coordinator.data and self.coordinator.data.presets and not self._preset:
            return True
        return False

    # TODO button to run diagonse or calibration?
