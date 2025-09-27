"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

from .data import VogelsMotionMountPresetData
from dataclasses import replace

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up the Numbers for distance, rotation, tv width and preset (distance, rotation)."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    async_add_entities(
        [
            DistanceNumber(coordinator),
            RotationNumber(coordinator),
            TVWidthNumber(coordinator),
            *[
                PresetDistanceNumber(coordinator, preset_index)
                for preset_index in range(7)
            ],
            *[
                PresetRotationNumber(coordinator, preset_index)
                for preset_index in range(7)
            ],
        ]
    )


class DistanceNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """NumberEntity to set the distance."""

    _attr_unique_id = "distance"
    _attr_translation_key = _attr_unique_id
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:ruler"

    @property
    def native_value(self):
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None
        if self.coordinator.data.requested_distance is not None:
            return self.coordinator.data.requested_distance
        return self.coordinator.data.distance

    async def async_set_native_value(self, value: float) -> None:
        """Set the value from the UI."""
        await self.coordinator.set_distance(int(value))


class RotationNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """NumberEntity to set the rotation."""

    _attr_unique_id = "rotation"
    _attr_translation_key = _attr_unique_id
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -100
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:angle-obtuse"

    @property
    def native_value(self):  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the state of the entity."""
        if not self.coordinator.data:
            return None
        if self.coordinator.data.requested_rotation is not None:
            return self.coordinator.data.requested_rotation
        return self.coordinator.data.rotation

    async def async_set_native_value(self, value: float) -> None:
        """Set the value from the UI."""
        await self.coordinator.set_rotation(int(value))


class TVWidthNumber(VogelsMotionMountBleBaseEntity, NumberEntity):
    """NumberEntity to set the TV width."""

    _attr_unique_id = "tv_width"
    _attr_translation_key = _attr_unique_id
    _attr_native_unit_of_measurement = "cm"
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1
    _attr_native_max_value = 1000
    _attr_icon = "mdi:television-box"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self):
        """Return the current value."""
        return self.coordinator.data.tv_width

    @property
    def available(self) -> bool:
        """Set availability if preset exists and user has permission."""
        return self.coordinator.data.permissions.change_settings

    async def async_set_native_value(self, value: float) -> None:
        """Set the value from the UI."""
        await self.coordinator.set_tv_width(int(value))


class PresetDistanceNumber(VogelsMotionMountBlePresetBaseEntity, NumberEntity):
    """NumberEntity to set distance of a preset."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:ruler"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_{preset_index}_distance"
        self._attr_translation_key = "preset_distance_custom"

    @property
    def available(self) -> bool:
        """Set availability if preset exists and user has permission."""
        return super().available and self.coordinator.data.permissions.change_presets

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset.data:
            return self._preset.data.distance
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value from the UI."""
        preset_data = self._preset.data
        if preset_data is None:
            preset_data = VogelsMotionMountPresetData(
                name=str(self._preset_index),
                distance=0,
                rotation=0,
            )
        await self.coordinator.set_preset(
            replace(self._preset, data=replace(preset_data, distance=(int(value))))
        )


class PresetRotationNumber(VogelsMotionMountBlePresetBaseEntity, NumberEntity):
    """NumberEntity to set rotation of a preset."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -100
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:angle-obtuse"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"preset_{preset_index}_rotation"
        self._attr_translation_key = "preset_rotation_custom"

    @property
    def available(self) -> bool:
        """Set availability if preset exists and user has permission."""
        return super().available and self.coordinator.data.permissions.change_presets

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset.data:
            return self._preset.data.rotation
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value from the UI."""
        preset_data = self._preset.data
        if preset_data is None:
            preset_data = VogelsMotionMountPresetData(
                name=str(self._preset_index),
                distance=0,
                rotation=0,
            )
        await self.coordinator.set_preset(
            replace(self._preset, data=replace(preset_data, rotation=(int(value))))
        )
