"""Button entities to define actions for Vogels Motion Mount BLE entities."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from typing import Any

from . import VogelsMotionMountBleConfigEntry
from .api import VogelsMotionMountActionType, VogelsMotionMountPinSettings
from .base import VogelsMotionMountBleBaseEntity
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
            MultiPinFeatureChangePresetsSwitch(coordinator),
            MultiPinFeatureChangeNameSwitch(coordinator),
            MultiPinFeatureDisableChannelSwitch(coordinator),
            MultiPinFeatureChangeTvOnOffDetectionSwitch(coordinator),
            MultiPinFeatureChangeDefaultPositionSwitch(coordinator),
            MultiPinFeatureStartCalibrationSwitch(coordinator),
        ]
    )


class MultiPinFeatureChangePresetsSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature change presets."""

    _attr_unique_id = "change_presets"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:security"

    @property
    def available(self) -> bool:  # type: ignore
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None
            and self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
            )
        )

    @property
    def is_on(self) -> bool:  # type: ignore
        """Returns on if change_presets is enabled."""
        if self.coordinator.data.multi_pin_features is not None:
            return self.coordinator.data.multi_pin_features.change_presets
        return False

    async def async_turn_on(self, **_: Any):
        """Turn the entity on."""
        await self.async_toggle()

    async def async_turn_off(self, **_: Any):
        """Turn the entity off."""
        await self.async_toggle()

    async def async_toggle(self, **_: Any):
        """Toggle if change presets is on or off."""
        await self.coordinator.api.set_multi_pin_features(change_presets=not self.is_on)


class MultiPinFeatureChangeNameSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature change name."""

    _attr_unique_id = "change_name"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:security"

    @property
    def available(self) -> bool:  # type: ignore
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None
            and self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
            )
        )

    @property
    def is_on(self) -> bool:  # type: ignore
        """Returns on if change presets is enabled."""
        if self.coordinator.data.multi_pin_features is not None:
            return self.coordinator.data.multi_pin_features.change_name
        return False

    async def async_turn_on(self, **_: Any):
        """Turn the entity on."""
        await self.async_toggle()

    async def async_turn_off(self, **_: Any):
        """Turn the entity off."""
        await self.async_toggle()

    async def async_toggle(self, **_: Any):
        """Toggle if change name is on or off."""
        await self.coordinator.api.set_multi_pin_features(change_name=not self.is_on)


class MultiPinFeatureDisableChannelSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature disable channel."""

    _attr_unique_id = "disable_channel"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:security"

    @property
    def available(self) -> bool:  # type: ignore
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None
            and self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
            )
        )

    @property
    def is_on(self) -> bool:  # type: ignore
        """Returns on if disable channel is enabled."""
        if self.coordinator.data.multi_pin_features is not None:
            return self.coordinator.data.multi_pin_features.disable_channel
        return False

    async def async_turn_on(self, **_: Any):
        """Turn the entity on."""
        await self.async_toggle()

    async def async_turn_off(self, **_: Any):
        """Turn the entity off."""
        await self.async_toggle()

    async def async_toggle(self, **_: Any):
        """Toggle if disable channeld is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            disable_channel=not self.is_on
        )


class MultiPinFeatureChangeTvOnOffDetectionSwitch(
    VogelsMotionMountBleBaseEntity, SwitchEntity
):
    """Set up the Switch to change multi pin feature change tv on off detection."""

    _attr_unique_id = "change_tv_on_off_detection"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:security"

    @property
    def available(self) -> bool:  # type: ignore
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None
            and self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
            )
        )

    @property
    def is_on(self) -> bool:  # type: ignore
        """Returns on if change tv on off detection is enabled."""
        if self.coordinator.data.multi_pin_features is not None:
            return self.coordinator.data.multi_pin_features.change_tv_on_off_detection
        return False

    async def async_turn_on(self, **_: Any):
        """Turn the entity on."""
        await self.async_toggle()

    async def async_turn_off(self, **_: Any):
        """Turn the entity off."""
        await self.async_toggle()

    async def async_toggle(self, **_: Any):
        """Toggle if change tv on off detection is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            change_tv_on_off_detection=not self.is_on
        )


class MultiPinFeatureChangeDefaultPositionSwitch(
    VogelsMotionMountBleBaseEntity, SwitchEntity
):
    """Set up the Switch to change multi pin feature change default position."""

    _attr_unique_id = "change_default_position"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:security"

    @property
    def available(self) -> bool:  # type: ignore
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None
            and self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
            )
        )

    @property
    def is_on(self) -> bool:  # type: ignore
        """Returns on if change default position is enabled."""
        if self.coordinator.data.multi_pin_features is not None:
            return self.coordinator.data.multi_pin_features.change_default_position
        return False

    async def async_turn_on(self, **_: Any):
        """Turn the entity on."""
        await self.async_toggle()

    async def async_turn_off(self, **_: Any):
        """Turn the entity off."""
        await self.async_toggle()

    async def async_toggle(self, **_: Any):
        """Toggle if change default position is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            change_default_position=not self.is_on
        )


class MultiPinFeatureStartCalibrationSwitch(
    VogelsMotionMountBleBaseEntity, SwitchEntity
):
    """Set up the Switch to change multi pin feature start calibration."""

    _attr_unique_id = "start_calibration"
    _attr_translation_key = _attr_unique_id
    _attr_icon = "mdi:security"

    @property
    def available(self) -> bool:  # type: ignore
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None
            and self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
            and self.coordinator.api.has_permission(
                action_type=VogelsMotionMountActionType.Settings,
            )
        )

    @property
    def is_on(self) -> bool:  # type: ignore
        """Returns on if change start calibration is enabled."""
        if self.coordinator.data.multi_pin_features is not None:
            return self.coordinator.data.multi_pin_features.start_calibration
        return False

    async def async_turn_on(self, **_: Any):
        """Turn the entity on."""
        await self.async_toggle()

    async def async_turn_off(self, **_: Any):
        """Turn the entity off."""
        await self.async_toggle()

    async def async_toggle(self, **_: Any):
        """Toggle if start calibration is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            start_calibration=not self.is_on
        )
