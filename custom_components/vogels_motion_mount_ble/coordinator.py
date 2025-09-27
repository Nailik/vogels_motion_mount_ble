"""Coordinator for Vogels Motion Mount BLE integration in order to communicate with client."""

from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
import logging

from bleak.backends.device import BLEDevice

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import VogelsMotionMountBluetoothClient
from .const import CONF_PIN, DOMAIN
from .data import (
    VogelsMotionMountAutoMoveType,
    VogelsMotionMountData,
    VogelsMotionMountMultiPinFeatures,
    VogelsMotionMountPermissions,
    VogelsMotionMountPinSettings,
    VogelsMotionMountPreset,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


class VogelsMotionMountBleCoordinator(DataUpdateCoordinator[VogelsMotionMountData]):
    """Vogels Motion Mount BLE coordinator."""

    # -------------------------------
    # region Setup
    # -------------------------------

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        device: BLEDevice,
        unsub_options_update_listener: Callable[[], None],
    ) -> None:
        """Initialize coordinator and setup client."""
        _LOGGER.debug("Startup coordinator with %s", config_entry.data)

        # Store setup data
        self._unsub_options_update_listener = unsub_options_update_listener
        self.address = device.address

        # Create client
        self._client = VogelsMotionMountBluetoothClient(
            pin=config_entry.data.get(CONF_PIN),
            device=device,
            permission_callback=self._permissions_changed,
            connection_callback=self._connection_changed,
            distance_callback=self._distance_changed,
            rotation_callback=self._rotation_changed,
        )

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.title,
            config_entry=config_entry,
            update_method=self._read_data,
            update_interval=timedelta(minutes=5),
        )
        _LOGGER.debug("Coordinator startup finished")

    async def unload(self):
        """Disconnect and unload."""
        _LOGGER.debug("unload coordinator")
        self._unsub_options_update_listener()
        await self._client.disconnect()

    async def refresh_data(self):
        """Load data form client."""
        await self._async_update_data()

    # -------------------------------
    # region Control
    # -------------------------------

    async def disconnect(self):
        """Disconnect form client."""
        await self._client.disconnect()

    async def select_preset(self, preset_index: int):
        """Select a preset to move to."""
        await self._client.select_preset(preset_index)

    async def start_calibration(self):
        """Start calibration process."""
        await self._client.start_calibration()

    # -------------------------------
    # region Config
    # -------------------------------


    async def request_distance(self, distance: int):
        """Request a distance to move to."""
        await self._client.request_distance(distance)
        self.async_set_updated_data(replace(self.data, requested_distance=distance))

    async def request_rotation(self, rotation: int):
        """Request a rotation to move to."""
        await self._client.request_rotation(rotation)
        self.async_set_updated_data(replace(self.data, requested_rotation=rotation))

    async def set_authorised_user_pin(self, pin: str):
        """Set or remove pin for authorised user."""
        await self._client.set_authorised_user_pin(pin)
        remove = pin == "0000"
        pin_setting = await self._client.read_pin_settings()
        if remove and pin_setting != VogelsMotionMountPinSettings.Deactivated:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_remove_authorised_user_pin",
                translation_placeholders={
                    "actual": str(pin_setting),
                    "expected": str(VogelsMotionMountPinSettings.Deactivated),
                },
            )
        if not remove and pin_setting == VogelsMotionMountPinSettings.Deactivated:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_authorised_user_pin",
                translation_placeholders={
                    "actual": str(pin_setting),
                    "expected": str(VogelsMotionMountPinSettings.Deactivated),
                },
            )
        await self.disconnect()
        self.async_set_updated_data(await self._async_update_data())

    async def set_automove(self, automove: VogelsMotionMountAutoMoveType):
        """Set type of automove."""
        await self._client.set_automove(automove)
        actual = await self._client.read_automove()
        self.async_set_updated_data(replace(self.data, automove=actual))
        if actual != automove:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_automove",
                translation_placeholders={
                    "expected": str(automove),
                    "actual": str(actual),
                },
            )

    async def set_freeze_preset(self, preset_index: int):
        """Set a preset to move to when automove is executed."""
        await self._client.set_freeze_preset(preset_index)
        actual = await self._client.read_freeze_preset_index()
        self.async_set_updated_data(replace(self.data, freeze_preset_index=actual))
        if actual != preset_index:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_freeze_preset_index",
                translation_placeholders={
                    "expected": str(preset_index),
                    "actual": str(actual),
                },
            )

    async def set_multi_pin_features(self, features: VogelsMotionMountMultiPinFeatures):
        """Set features the authorised user is eligible to change."""
        await self._client.set_multi_pin_features(features)
        actual = await self._client.read_multi_pin_features()
        self.async_set_updated_data(replace(self.data, multi_pin_features=actual))
        if actual != features:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_multi_pin_features",
                translation_placeholders={
                    "expected": str(features),
                    "actual": str(actual),
                },
            )

    async def set_name(self, name: str):
        """Set name of the Vogels Motion Mount."""
        await self._client.set_name(name)
        actual = await self._client.read_name()
        self.async_set_updated_data(replace(self.data, name=actual))
        if actual != name:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_name",
                translation_placeholders={
                    "expected": str(name),
                    "actual": str(actual),
                },
            )

    async def set_preset(self, preset: VogelsMotionMountPreset):
        """Set the data of a preset."""
        await self._client.set_preset(preset)
        actual = await self._client.read_preset(preset.index)
        presets = self.data.presets.copy()
        presets[preset.index] = actual
        self.async_set_updated_data(replace(self.data, presets=presets))
        if actual != preset:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_preset",
                translation_placeholders={
                    "expected": str(preset),
                    "actual": str(actual),
                },
            )

    async def set_supervisior_pin(self, pin: str):
        """Set or remove pin for a supervisior."""
        await self._client.set_supervisior_pin(pin)
        remove = pin == "0000"
        pin_setting = await self._client.read_pin_settings()
        if remove and pin_setting != VogelsMotionMountPinSettings.Single:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_remove_supervisior_pin",
                translation_placeholders={
                    "actual": str(pin_setting),
                    "expected": str(VogelsMotionMountPinSettings.Single),
                },
            )
        if not remove and pin_setting != VogelsMotionMountPinSettings.Multi:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_supervisior_pin",
                translation_placeholders={
                    "actual": str(pin_setting),
                    "expected": str(VogelsMotionMountPinSettings.Multi),
                },
            )
        await self.disconnect()
        self.async_set_updated_data(await self._async_update_data())

    async def set_tv_width(self, width: int):
        """Set the width of the tv."""
        await self._client.set_tv_width(width)
        actual = await self._client.read_tv_width()
        self.async_set_updated_data(replace(self.data, tv_width=actual))
        if actual != width:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_saved_tv_width",
                translation_placeholders={
                    "expected": str(width),
                    "actual": str(actual),
                },
            )

    # -------------------------------
    # region Notifications
    # -------------------------------

    def _permissions_changed(self, permissions: VogelsMotionMountPermissions):
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, permissions=permissions))

    def _connection_changed(self, connected: bool):
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, connected=connected))

    def _distance_changed(self, distance: int):
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, distance=distance))

    def _rotation_changed(self, rotation: int):
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, rotation=rotation))

    # -------------------------------
    # region internal
    # -------------------------------

    async def _read_data(self) -> VogelsMotionMountData:
        """Fetch data from device."""
        return VogelsMotionMountData(
            automove=await self._client.read_automove(),
            connected=self.data.connected if self.data is not None else False,
            distance=await self._client.read_distance(),
            freeze_preset_index=await self._client.read_freeze_preset_index(),
            multi_pin_features=await self._client.read_multi_pin_features(),
            name=await self._client.read_name(),
            pin_setting=await self._client.read_pin_settings(),
            presets=await self._client.read_presets(),
            rotation=await self._client.read_rotation(),
            tv_width=await self._client.read_tv_width(),
            versions=await self._client.read_versions(),
            permissions=await self._client.read_permissions(),
        )
