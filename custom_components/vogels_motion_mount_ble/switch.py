"""Button entities to define actions for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import VogelsMotionMountBleConfigEntry
from .api import VogelsMotionMountPinSettings
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_SET_MULTI_PIN_FEATURES,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_PRESET_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_NAME_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_DISABLE_CHANNEL_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_TV_ON_OFF_DETECTION_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_DEFAULT_PRESET_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_START_CALIBRATION_ID,
    )
from .coordinator import VogelsMotionMountBleCoordinator
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _set_multi_pin_features(call: ServiceCall) -> None:
    _LOGGER.debug("Set multi pin features change presets service called with data: %s", call.data)
    await get_coordinator(call).api.set_multi_pin_features(
        change_presets = call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_PRESET_ID),
        change_name = call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_NAME_ID),
        disable_channel = call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_DISABLE_CHANNEL_ID),
        change_tv_on_off_detection = call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_TV_ON_OFF_DETECTION_ID),
        change_default_position = call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_DEFAULT_PRESET_ID),
        start_calibration = call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_START_CALIBRATION_ID),
    )

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the RefreshData and SelectPreset buttons."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_MULTI_PIN_FEATURES,
        _set_multi_pin_features,
    )

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

    _attr_unique_id = "multi_pin_feature_change_presets"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None and
            self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.multi_pin_features.change_presets

    async def async_toggle(self, **kwargs):
        """Toggle if change presets is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            change_presets=not self.is_on
        )

class MultiPinFeatureChangeNameSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature change name."""

    _attr_unique_id = "multi_pin_feature_change_name"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None and
            self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.multi_pin_features.change_name

    async def async_toggle(self, **kwargs):
        """Toggle if change name is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            change_name=not self.is_on
        )

class MultiPinFeatureDisableChannelSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature disable channel."""

    _attr_unique_id = "multi_pin_feature_disable_channel"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None and
            self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.multi_pin_features.disable_channel

    async def async_toggle(self, **kwargs):
        """Toggle if disable channeld is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            disable_channel=not self.is_on
        )

class MultiPinFeatureChangeTvOnOffDetectionSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature change tv on off detection."""

    _attr_unique_id = "multi_pin_feature_change_tv_on_off_detection"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None and
            self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.multi_pin_features.change_tv_on_off_detection

    async def async_toggle(self, **kwargs):
        """Toggle if change tv on off detection is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            change_tv_on_off_detection=not self.is_on
        )

class MultiPinFeatureChangeDefaultPositionSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature change default position."""

    _attr_unique_id = "multi_pin_feature_change_default_position"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None and
            self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.multi_pin_features.change_default_position

    async def async_toggle(self, **kwargs):
        """Toggle if change default position is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            change_default_position=not self.is_on
        )

class MultiPinFeatureStartCalibrationSwitch(VogelsMotionMountBleBaseEntity, SwitchEntity):
    """Set up the Switch to change multi pin feature start calibration."""

    _attr_unique_id = "multi_pin_feature_start_calibration"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability of multi pin features."""
        return (
            self.coordinator.data.pin_setting is not None and
            self.coordinator.data.pin_setting is VogelsMotionMountPinSettings.Multi
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.multi_pin_features.start_calibration

    async def async_toggle(self, **kwargs):
        """Toggle if start calibration is on or off."""
        await self.coordinator.api.set_multi_pin_features(
            start_calibration=not self.is_on
        )