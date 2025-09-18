"""Bluetooth api to connect to Vogels MotionMount."""

import asyncio
from dataclasses import dataclass, field, replace
from enum import Enum
import logging
import struct
from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak import BleakClient
from bleak.exc import BleakDeviceNotFoundError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from collections.abc import Callable
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from typing import Any

from .const import (
    CHAR_AUTHENTICATE_UUID,
    CHAR_AUTOMOVE_OFF_OPTIONS,
    CHAR_AUTOMOVE_ON_OPTIONS,
    CHAR_AUTOMOVE_UUID,
    CHAR_CHANGE_PIN_UUID,
    CHAR_DISTANCE_UUID,
    CHAR_FREEZE_UUID,
    CHAR_MULTI_PIN_FEATURES_UUID,
    CHAR_NAME_UUID,
    CHAR_PIN_CHECK_UUID,
    CHAR_PIN_SETTINGS_UUID,
    CHAR_PRESET_NAMES_UUIDS,
    CHAR_PRESET_UUID,
    CHAR_PRESET_UUIDS,
    CHAR_ROTATION_UUID,
    CHAR_VERSIONS_CEB_UUID,
    CHAR_VERSIONS_MCP_UUID,
    CHAR_WIDTH_UUID,
)


@dataclass
class VogelsMotionMountPreset:
    """Holds the data of a preset."""

    index: int
    name: str
    distance: int
    rotation: int


class VogelsMotionMountPinSettings(Enum):
    """Defines the possible pin settings."""

    Deactivated = 12
    Single = 13
    Multi = 15


class VogelsMotionMountPinType(Enum):
    """Defines the possible pin type."""

    Authorized_user = 1
    Supervisior = 2


class VogelsMotionMountAuthenticationType(Enum):
    """Defines the authentication options."""

    Wrong = 0
    Missing = 1
    Control = 2
    Full = 3


class VogelsMotionMountAutoMoveType(Enum):
    """Defines the authentication options."""

    Off = "off"
    Hdmi_1 = "hdmi_1"
    Hdmi_2 = "hdmi_2"
    Hdmi_3 = "hdmi_3"
    Hdmi_4 = "hdmi_4"
    Hdmi_5 = "hdmi_5"


@dataclass
class MultiPinFeatures:
    """Holds the information what the pin is verified for."""

    change_presets: bool
    change_name: bool
    disable_channel: bool
    change_tv_on_off_detection: bool
    change_default_position: bool
    start_calibration: bool


class SettingsRequestType(Enum):
    """Defines types for changing settings request in order to check if user is authenticated."""

    change_presets = 0
    change_name = 1
    disable_channel = 2
    change_tv_on_off_detection = 3
    change_default_position = 4
    start_calibration = 5


class VogelsMotionMountActionType(Enum):
    """Defines the possible actions."""

    Control = 0  # control the device
    Settings = 1  # change settingsVogelsMotionActionType(Enum):


@dataclass
class VogelsMotionMountData:
    """Holds the data of the device."""

    connected: bool = False
    name: str | None = None
    distance: int | None = None
    rotation: int | None = None
    requested_distance: int | None = None
    requested_rotation: int | None = None
    presets: dict[int, VogelsMotionMountPreset | None] = field(
        default_factory=lambda: dict[int, VogelsMotionMountPreset | None]()
    )
    width: int | None = None
    freeze_preset_index: int | None = None
    automove_type: VogelsMotionMountAutoMoveType | None = None
    automove_id: int | None = None
    pin_setting: VogelsMotionMountPinSettings | None = None
    ceb_bl_version: str | None = None
    mcp_hw_version: str | None = None
    mcp_bl_version: str | None = None
    mcp_fw_version: str | None = None
    multi_pin_features: MultiPinFeatures | None = None
    auth_type: VogelsMotionMountAuthenticationType | None = None


class APIConnectionError(HomeAssistantError):
    """Exception class for unknown connection error."""


class APIConnectionDeviceNotFoundError(ConfigEntryNotReady):
    """Exception class for connection error when device was not found."""


class APIAuthenticationError(ConfigEntryAuthFailed):
    """Exception class if user is not authorized to do this action."""

    def __init__(self, message: str, cooldown: int = 0) -> None:
        """Create Authentication error with information about cooldown time."""
        super().__init__(message)
        self.cooldown = cooldown


class APISettingsChangeNotStoredError(HomeAssistantError):
    """Exception class if changed settings are not saved on vogels motion mount."""


# endregion


# internal classes


# endregion
# region Public api


class API:
    """Bluetooth API."""

    def __init__(
        self,
        hass: HomeAssistant,
        mac: str,
        pin: str | None,
        callback: Callable[[VogelsMotionMountData], None] | None,
    ) -> None:
        """Set up the default data."""
        self._logger = logging.getLogger(f"{__name__}.{mac}")
        self._logger.debug("Setup bluetooth api with mac %s and pin %s", mac, pin)
        self._hass = hass
        self._mac = mac
        self._pin = pin
        self._callback = callback
        self._data = VogelsMotionMountData()
        self._device: BLEDevice | None = None
        self._client: BleakClient | None = None
        # store last validated pin type to reuse
        self._pin_type: VogelsMotionMountPinType | None = None
        # store authentication cooldown
        self._authentication_cooldown: int = 0

    async def test_connection(self):
        """Test connection to the BLE device once using BleakClient and disconnects immediately."""
        self._logger.debug("Test connection")
        if not self._initialize_device():
            raise APIConnectionDeviceNotFoundError

        try:
            # make sure we are disconnected before testing connection otherwise authentication might not be tested
            await self.disconnect()
            assert self._device is not None
            self._logger.debug("Device found attempting to connect")
            self._client = await establish_connection(
                client_class=BleakClientWithServiceCache,
                device=self._device,
                name=self._device.name or "Unknown Device",
            )
            await self._authenticate()
            self._logger.debug("Connected")
            await self.disconnect()
        except BleakDeviceNotFoundError as err:
            self._logger.error("Failed to connect, device not found")
            raise APIConnectionDeviceNotFoundError from err
        except APIAuthenticationError as err:
            self._logger.error("Failed to connect wrong authentication")
            raise err from err
        except Exception as err:
            self._logger.error("Failed to connect")
            raise APIConnectionError from err

    async def disconnect(self):
        """Disconnect from the BLE Device."""
        self._logger.debug("Disconnecting")
        if self._client is not None:
            await self._client.disconnect()
        self._logger.debug("Disconnected!")

    async def unload(self):
        """Unload the api, disconnect and delete ble classes."""
        self._logger.debug("Unload")
        await self.disconnect()
        self._device = None
        self._client = None
        bluetooth.async_rediscover_address(self._hass, self._mac)

    async def refresh_data(self):
        """Read data from BLE device, connects if necessary."""
        if self._client and self._client.is_connected:
            # Authenticate in order to make it visible that authentication does not work
            await self._authenticate()
            await self._read_current_data()
        else:
            # connect will automatically load data
            await self._connect()

    # region Control

    async def set_distance(self, distance: int):
        """Set the distance to move the MotionMount to."""
        self._logger.debug("Set distance to %s", distance)

        if distance not in range(101):
            raise ServiceValidationError(
                f"Invalid distance {distance} must be in range(101)."
            )

        await self._connect(
            type=VogelsMotionMountActionType.Control,
            char_uuid=CHAR_DISTANCE_UUID,
            data=int(distance).to_bytes(2, byteorder="big"),
        )
        self._update(requested_distance=distance)

    async def set_rotation(self, rotation: int):
        """Set the rotation move the MotionMount to."""
        self._logger.debug("Set rotation to %s", rotation)

        if rotation not in range(-100, 101):
            raise ServiceValidationError(
                f"Invalid rotation {rotation} must be in range(-100,101)."
            )

        await self._connect(
            type=VogelsMotionMountActionType.Control,
            char_uuid=CHAR_ROTATION_UUID,
            data=int(rotation).to_bytes(2, byteorder="big", signed=True),
        )
        self._logger.debug(
            "write rotation  %s",
            int(rotation).to_bytes(2, byteorder="big", signed=True),
        )
        self._update(requested_rotation=rotation)

    async def select_default_preset(self):
        """Select a preset index to move the MotionMount to."""
        self._logger.debug("Select default preset")
        await self._connect(
            type=VogelsMotionMountActionType.Control,
            char_uuid=CHAR_PRESET_UUID,
            data=bytes([0]),
        )

    async def select_preset(self, preset_index: int):
        """Select a preset index to move the MotionMount to."""
        self._logger.debug("Select preset %s", preset_index)

        if (
            preset_index not in range(7)
            and self._data.presets[preset_index] is not None
        ):
            raise ServiceValidationError(
                f"Invalid preset index {preset_index} should be in range(7)."
            )

        if self._data.presets[preset_index] is None:
            raise ServiceValidationError(
                f"Preset at index {preset_index} doesn't exist."
            )

        await self._connect(
            type=VogelsMotionMountActionType.Control,
            char_uuid=CHAR_PRESET_UUID,
            # Preset IDs are 1-based because 0 is the default preset
            data=bytes([preset_index + 1]),
        )

    # endregion
    # region Settings

    def has_permission(
        self,
        action_type: VogelsMotionMountActionType,
        settings_request_type: SettingsRequestType | None = None,
    ) -> bool:
        if self._data.auth_type == VogelsMotionMountAuthenticationType.Full:
            return True
        if (
            self._data.auth_type == VogelsMotionMountAuthenticationType.Control
            and action_type == VogelsMotionMountActionType.Control
        ):
            return True

        if self._data.auth_type == VogelsMotionMountAuthenticationType.Control:
            if self._data.multi_pin_features is None:
                self._logger.warning("Unable to check multi pin features.")
                return False
            if settings_request_type == SettingsRequestType.change_presets:
                return self._data.multi_pin_features.change_presets
            elif settings_request_type == SettingsRequestType.change_name:
                return self._data.multi_pin_features.change_name
            elif settings_request_type == SettingsRequestType.disable_channel:
                return self._data.multi_pin_features.disable_channel
            elif (
                settings_request_type == SettingsRequestType.change_tv_on_off_detection
            ):
                return self._data.multi_pin_features.change_tv_on_off_detection
            elif settings_request_type == SettingsRequestType.change_default_position:
                return self._data.multi_pin_features.change_default_position
            elif settings_request_type == SettingsRequestType.start_calibration:
                return self._data.multi_pin_features.start_calibration

        return False

    async def set_name(self, name: str):
        """Set the bluetooth name for the deice."""
        self._logger.debug("Change name to %s", name)
        if len(name) > 20:
            raise ServiceValidationError(
                f"Name {name} too long, max length is 20 characters."
            )

        newname = bytearray(name.encode("utf-8"))[:20].ljust(20, b"\x00")
        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_name,
            char_uuid=CHAR_NAME_UUID,
            data=newname,
        )
        await self._read_name()
        if self._data.name != name:
            raise ServiceValidationError(
                f"Name change not saved on device. Expected {name} actual {self._data.name}."
            )

    async def set_preset(
        self,
        preset_index: int,
        name: str | None = None,
        distance: int | None = None,
        rotation: int | None = None,
    ):
        """Change data of a preset, name has a max length of 32 characters."""
        self._logger.debug(
            "Change preset %s to name %s, distance to %s and rotation to %s",
            preset_index,
            name,
            distance,
            rotation,
        )

        if (
            preset_index not in range(7)
            and self._data.presets[preset_index] is not None
        ):
            raise ServiceValidationError(
                f"Invalid preset index {preset_index} should be in range(7)."
            )

        if distance not in range(101):
            raise ServiceValidationError(
                f"Invalid distance {distance} must be in range(101)."
            )

        if rotation not in range(-100, 101):
            raise ServiceValidationError(
                f"Invalid rotation {rotation} must be in range(-100,101)."
            )

        preset = self._data.presets[preset_index]

        new_name: str = (
            name
            if name is not None
            else preset.name
            if preset is not None
            else f"{preset_index}"
        )

        if len(new_name) > 32:
            raise ServiceValidationError(
                f"Name {name} too long, max length is 32 characters."
            )

        new_distance = (
            distance
            if distance is not None
            else preset.distance
            if preset is not None
            else 0
        )
        new_rotation = (
            rotation
            if rotation is not None
            else preset.rotation
            if preset is not None
            else 0
        )

        distance_bytes = int(new_distance).to_bytes(2, byteorder="big")
        rotation_bytes = int(new_rotation).to_bytes(2, byteorder="big", signed=True)
        name_bytes = new_name.encode("utf-8")

        data = b"\x01" + distance_bytes + rotation_bytes + name_bytes

        # write first 20 bytes, distance, rotation and beginning of name
        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_presets,
            char_uuid=CHAR_PRESET_UUIDS[preset_index],
            data=data[:20].ljust(20, b"\x00"),
        )
        # write rest of name
        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_presets,
            char_uuid=CHAR_PRESET_NAMES_UUIDS[preset_index],
            data=data[20:].ljust(17, b"\x00"),
        )

        await self._read_preset(preset_index)
        expected_data = VogelsMotionMountPreset(
            index=preset_index,
            name=new_name,
            distance=new_distance,
            rotation=new_rotation,
        )
        if self._data.presets[preset_index] != expected_data:
            raise ServiceValidationError(
                f"Preset change not saved on device. Expected {expected_data} actual {self._data.presets[preset_index]}."
            )

    async def delete_preset(self, preset_index: int):
        """Delete a preset by index to move the MotionMount to."""
        self._logger.debug("Delete preset %s", preset_index)

        if (
            preset_index not in range(7)
            and self._data.presets[preset_index] is not None
        ):
            raise ServiceValidationError(
                f"Invalid preset index {preset_index} should be in range(7)."
            )

        if self._data.presets[preset_index] is None:
            raise ServiceValidationError(
                f"Preset at index {preset_index} doesn't exist."
            )

        newpresets = dict(self._data.presets)
        newpresets[preset_index] = None
        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_presets,
            char_uuid=CHAR_PRESET_UUIDS[preset_index],
            data=bytes(0x01).ljust(20, b"\x00"),
        )
        await self._read_preset(preset_index)
        if self._data.presets[preset_index] is not None:
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Preset delete not saved on device. Expected None actual {self._data.presets[preset_index]}."
            )

    async def set_tv_width(self, width: int):
        """Select a preset index to move the MotionMount to."""
        self._logger.debug("Set width %s", width)

        if width not in range(1, 244):
            raise ServiceValidationError(f"Tv width {width} must be in range(1, 244).")

        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            char_uuid=CHAR_WIDTH_UUID,
            data=bytes([width]),
        )
        await self._read_width()
        if self._data.width != width:
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Width data not saved on device. Expected {width} actual {self._data.width}."
            )

    async def set_automove(self, id: str):
        """Select a automove option where None is off."""
        self._logger.debug("Set automove to %s", id)

        try:
            automove_type = VogelsMotionMountAutoMoveType(id)
        except ValueError as err:
            raise ServiceValidationError(
                f'AutoMove type {id} does not exist, must be any of "off", "hdmi_1", "hdmi_2", "hdmi_3", "hdmi_4", "hdmi_5".'
            ) from err

        if automove_type == VogelsMotionMountAutoMoveType.Off:
            new_id = CHAR_AUTOMOVE_OFF_OPTIONS[
                self._data.automove_id if self._data.automove_id is not None else 0
            ]
        else:
            automove_types = [
                VogelsMotionMountAutoMoveType.Hdmi_1,
                VogelsMotionMountAutoMoveType.Hdmi_2,
                VogelsMotionMountAutoMoveType.Hdmi_3,
                VogelsMotionMountAutoMoveType.Hdmi_4,
                VogelsMotionMountAutoMoveType.Hdmi_5,
            ]
            new_id = CHAR_AUTOMOVE_ON_OPTIONS[automove_types.index(automove_type)]

        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_tv_on_off_detection,
            char_uuid=CHAR_AUTOMOVE_UUID,
            data=int(new_id).to_bytes(2, byteorder="big"),
        )
        await self._read_automove()
        if (
            self._data.automove_id != new_id
            or self._data.automove_type != automove_type
        ):
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Automove data not saved on device. Expected id {new_id} actual {self._data.automove_id}, expected type {automove_type} actual {self._data.automove_type}."
            )

    async def set_authorised_user_pin(self, pin: str):
        """Set 4 digit pin for authorised users."""
        self._logger.debug("Set authorized user pin to %s", pin)
        remove = pin == "0000"

        if remove and self._data.pin_setting == VogelsMotionMountPinSettings.Multi:
            raise ServiceValidationError(
                "Authorised user pin cannot be deactivated when supervisior pin is set."
            )

        if len(pin) != 4:
            raise ServiceValidationError(
                "Authorised user pin is too long, max length 4 digits."
            )

        if not pin.isdigit():
            raise ServiceValidationError(
                "Authorised user pin contains non digit characters."
            )

        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            char_uuid=CHAR_CHANGE_PIN_UUID,
            data=self._encode_pin(int(pin), VogelsMotionMountPinType.Authorized_user),
        )
        await self._read_pin_settings()

        if (
            remove
            and self._data.pin_setting != VogelsMotionMountPinSettings.Deactivated
        ):
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Authorised user pin was not set removed. Expected pin settings {VogelsMotionMountPinSettings.Deactivated} actual  {self._data.pin_setting}."
            )

        if (
            not remove
            and self._data.pin_setting == VogelsMotionMountPinSettings.Deactivated
        ):
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Authorised user pin was not set removed. Expected pin settings {VogelsMotionMountPinSettings.Single} or {VogelsMotionMountPinSettings.Multi} actual  {self._data.pin_setting}."
            )
        # required to check if authentication is still valid
        await self.disconnect()
        await self.refresh_data()

    async def set_supervisior_pin(self, pin: str):
        """Set 4 digit pin for supervisior."""
        self._logger.debug("Set supervisior pin to %s", pin)
        remove = pin == "0000"

        if remove and self._data.pin_setting == VogelsMotionMountPinSettings.Single:
            raise ServiceValidationError(
                "Supervisior pin cannot be deactivated when supervisior pin is not set."
            )

        if self._data.pin_setting == VogelsMotionMountPinSettings.Deactivated:
            raise ServiceValidationError(
                "Supervisior pin cannot be set when authorized user pin is not set."
            )

        if len(pin) != 4:
            raise ServiceValidationError(
                "Supervisior pin is too long, max length 4 digits."
            )

        if not pin.isdigit():
            raise ServiceValidationError(
                "Supervisior pin contains non digit characters."
            )

        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            char_uuid=CHAR_CHANGE_PIN_UUID,
            data=self._encode_pin(int(pin), VogelsMotionMountPinType.Supervisior),
        )
        await self._read_pin_settings()

        if remove and self._data.pin_setting != VogelsMotionMountPinSettings.Single:
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Authorised user pin was not set removed. Expected pin settings {VogelsMotionMountPinSettings.Single} actual {self._data.pin_setting}."
            )

        if not remove and self._data.pin_setting != VogelsMotionMountPinSettings.Multi:
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Supervisior pin was not set. Expected pin settings {VogelsMotionMountPinSettings.Multi} actual {self._data.pin_setting}."
            )
        # required to check if authentication is still valid
        await self.disconnect()
        await self.refresh_data()

    async def set_freeze_preset(self, preset_index: int):
        """Set preset that is used for auto move freeze position."""
        self._logger.debug("Set freeze preset index to %s", preset_index)

        # take into account that there is a default preset
        if preset_index not in range(8):
            raise ServiceValidationError(
                f"Invalid preset index {preset_index} should be in range(8)."
            )

        if preset_index == 0 or self._data.presets[preset_index - 1] is None:
            raise ServiceValidationError(
                f"Preset at index {preset_index} doesn't exist."
            )

        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            settings_request_type=SettingsRequestType.change_default_position,
            char_uuid=CHAR_FREEZE_UUID,
            data=bytes([preset_index]),
        )
        await self._read_freeze_preset()
        if self._data.freeze_preset_index != preset_index:
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Freeze preset data not saved on device. Expected {preset_index} actual {self._data.freeze_preset_index}."
            )

    async def set_multi_pin_features(
        self,
        change_presets: bool | None = None,
        change_name: bool | None = None,
        disable_channel: bool | None = None,
        change_tv_on_off_detection: bool | None = None,
        change_default_position: bool | None = None,
        start_calibration: bool | None = None,
    ):
        """Set the pin settings."""
        self._logger.debug(
            "Set multi pin features to change_presets %s change_name %s disable_channel %s change_tv_on_off_detection %s change_default_position %s start_calibration  %s",
            change_presets,
            change_name,
            disable_channel,
            change_tv_on_off_detection,
            change_default_position,
            start_calibration,
        )

        multi_pin_features = self._data.multi_pin_features or MultiPinFeatures(
            change_presets=False,
            change_name=False,
            disable_channel=False,
            change_tv_on_off_detection=False,
            change_default_position=False,
            start_calibration=False,
        )

        new_change_presets = change_presets or multi_pin_features.change_presets
        new_change_name = change_name or multi_pin_features.change_name
        new_disable_channel = disable_channel or multi_pin_features.disable_channel
        new_change_tv_on_off_detection = (
            change_tv_on_off_detection or multi_pin_features.change_tv_on_off_detection
        )
        new_change_default_position = (
            change_default_position or multi_pin_features.change_default_position
        )
        new_start_calibration = (
            start_calibration or multi_pin_features.start_calibration
        )

        value = 0
        value |= int(new_change_presets) << 0
        value |= int(new_change_name) << 1
        value |= int(new_disable_channel) << 2
        value |= int(new_change_tv_on_off_detection) << 3
        value |= int(new_change_default_position) << 4
        value |= int(new_start_calibration) << 7

        await self._connect(
            type=VogelsMotionMountActionType.Settings,
            char_uuid=CHAR_MULTI_PIN_FEATURES_UUID,
            data=bytes([value]),
        )
        await self._read_multi_pin_features()
        new_multi_pin_features = MultiPinFeatures(
            change_presets=new_change_presets,
            change_name=new_change_name,
            disable_channel=new_disable_channel,
            change_tv_on_off_detection=new_change_tv_on_off_detection,
            change_default_position=new_change_default_position,
            start_calibration=new_start_calibration,
        )
        if self._data.multi_pin_features != new_multi_pin_features:
            self._update()
            raise APISettingsChangeNotStoredError(
                f"Multi pin features data not saved on device. Expected {new_multi_pin_features} actual {self._data.multi_pin_features}."
            )

    # endregion
    # endregion
    # region Private functions

    # initializes device and returns true if found
    def _initialize_device(self) -> bool:
        self._logger.debug("Initialize device")
        if self._device is None:
            self._device = bluetooth.async_ble_device_from_address(
                hass=self._hass,
                address=self._mac,
                connectable=True,
            )
            if self._device is None:
                return False
            self._client = BleakClient(
                address_or_ble_device=self._device,
                disconnected_callback=self._handle_disconnect,
                timeout=120,
            )
        result = self._client is not None
        self._logger.debug("Initialisation was %s", result)
        return result

    # connect and load data if new connection
    # checks authentication for this action type else raises an APIAuthenticationError error
    async def _connect(
        self,
        type: VogelsMotionMountActionType | None = None,
        settings_request_type: SettingsRequestType | None = None,
        char_uuid: str | None = None,
        data: bytes | None = None,
    ):
        if not self._initialize_device():
            raise APIConnectionDeviceNotFoundError("Device not found.")

        assert self._device is not None
        assert self._client is not None

        self._logger.debug("Connect")

        if self._client.is_connected:
            should_read_data = False
            self._logger.debug("Already connected, no need to connect again")
        else:
            should_read_data = True
            self._logger.debug("Connecting")

            self._client = await establish_connection(
                client_class=BleakClientWithServiceCache,
                device=self._device,
                name=self._device.name or "Unknown Device",
                disconnected_callback=self._handle_disconnect,
            )
            self._logger.debug("Connected!")

        self._update(connected=self._client.is_connected)

        await self._authenticate(
            type=type,
            settings_request_type=settings_request_type,
        )

        if char_uuid is not None and data is not None:
            self._logger.debug("Write data %s", data)
            # calls callback before loading data in order to run command with less delay
            await self._client.write_gatt_char(
                char_specifier=char_uuid,
                data=data,
                response=True,
            )

        if should_read_data:
            # only read data and setup notifications if this was a new connection
            await self._setup_notifications()
            await self._read_current_data()

    # encodes the pin depending on type
    def _encode_pin(self, pin: int, mode: VogelsMotionMountPinType) -> bytes:
        """Encode a PIN into 2-byte sequence for API.

        mode = "auth"   -> direct little-endian
        mode = "change" -> little-endian, high byte + 0x40
        """
        # Convert to little-endian bytes
        low = pin & 0xFF
        high = (pin >> 8) & 0xFF

        if mode == VogelsMotionMountPinType.Supervisior:
            high = (high + 0x40) & 0xFF  # add offset, wrap if >255

        return bytes([low, high])

    # check if authentication is full or only control or none at all, returns true if any, stores the auth type
    async def _check_authentication(self) -> bool:
        self._logger.debug("_check_authentication")
        assert self._client is not None

        _auth_info = await self._client.read_gatt_char(CHAR_PIN_CHECK_UUID)
        self._logger.debug("_check_authentication returns %s", _auth_info)
        if _auth_info.startswith(b"\x80\x80"):
            self._update(auth_type=VogelsMotionMountAuthenticationType.Full)
        elif _auth_info.startswith(b"\x80"):
            self._update(auth_type=VogelsMotionMountAuthenticationType.Control)
        else:
            code = struct.unpack("<I", _auth_info)[0]
            self._authentication_cooldown = max(0, 3 * code - 10)
            self._logger.warning(
                "Authentication wrong, expected wait time %s seconds.",
                self._authentication_cooldown,
            )
            return False
        return True

    # authenticate as a specific pin type
    # stores the pin_type if successful
    async def _authenticate_as(self, type: VogelsMotionMountPinType) -> bool:
        self._logger.debug("_authenticate_as %s", type)
        assert self._client is not None

        if self._pin is None:
            return False
        await self._client.write_gatt_char(
            CHAR_AUTHENTICATE_UUID, self._encode_pin(int(self._pin), type)
        )
        for attempt in range(4):
            if await self._check_authentication():
                self._pin_type = type
                self._logger.debug("_authenticate_as %s success", type)
                return True
            if attempt < 3:
                await asyncio.sleep(0.1)
        self._logger.debug("_authenticate_as %s fail", type)
        return False

    # authenticate the user for this action type
    # if already authenticated only checks for correct type
    # else tries to authenticate for supervisior first and then for authorized user
    async def _authenticate(
        self,
        type: VogelsMotionMountActionType | None = None,
        settings_request_type: SettingsRequestType | None = None,
    ):
        self._logger.debug("Authenticate")

        if await self._check_authentication():
            self._logger.debug("already authenticated!")

            # make sure multi pin features are up to date
            await self._read_multi_pin_features()
            # check for settings request permission
            if type is not None:
                if not self.has_permission(
                    action_type=type,
                    settings_request_type=settings_request_type,
                ):
                    raise APIAuthenticationError(
                        "Not authenticated for this settings action.",
                        self._authentication_cooldown,
                    )
            return

        # authentication required but no pin set
        if self._pin is None:
            self._update(auth_type=VogelsMotionMountAuthenticationType.Missing)
            await self.disconnect()
            raise APIAuthenticationError(
                "Authentication missing.", self._authentication_cooldown
            )

        authentication_types = (
            [
                VogelsMotionMountPinType.Authorized_user,
                VogelsMotionMountPinType.Supervisior,
            ]
            if self._pin_type == VogelsMotionMountPinType.Authorized_user
            else [
                VogelsMotionMountPinType.Supervisior,
                VogelsMotionMountPinType.Authorized_user,
            ]
        )

        for test_auth_type in authentication_types:
            if await self._authenticate_as(type=test_auth_type):
                if (
                    test_auth_type == VogelsMotionMountPinType.Authorized_user
                    and type == VogelsMotionMountActionType.Settings
                ):
                    # make sure multi pin features are up to date
                    await self._read_multi_pin_features()
                    if not self.has_permission(
                        action_type=type,
                        settings_request_type=settings_request_type,
                    ):
                        raise APIAuthenticationError(
                            "Not authenticated for this settings action.",
                            self._authentication_cooldown,
                        )
                return

        self._update(auth_type=VogelsMotionMountAuthenticationType.Wrong)
        await self.disconnect()
        raise APIAuthenticationError("Invalid pin.", self._authentication_cooldown)

    # disconnect from the client
    def _handle_disconnect(self, _: BleakClient):
        self._logger.debug("Device disconnected!")
        if self._client is not None:
            self._update(connected=self._client.is_connected)

    # Notifications in order to get updates from device via ble notify.
    async def _setup_notifications(self):
        self._logger.debug("Setup notifications")
        assert self._client is not None
        await self._client.start_notify(
            char_specifier=CHAR_DISTANCE_UUID,
            callback=self._handle_distance_change,
        )
        await self._client.start_notify(
            char_specifier=CHAR_ROTATION_UUID,
            callback=self._handle_rotation_change,
        )

    # Read all data from device.
    async def _read_current_data(self):
        self._logger.debug("Read current data")
        assert self._client is not None
        await self._read_name()
        await self._read_distance()
        self._handle_rotation_change(
            None, await self._client.read_gatt_char(CHAR_ROTATION_UUID)
        )
        for preset_index in range(7):
            await self._read_preset(preset_index)
        await self._read_width()
        await self._read_freeze_preset()
        await self._read_automove()
        await self._read_pin_settings()
        await self._read_multi_pin_features()
        await self._read_version_ceb()
        await self._read_version_mcp()

    # Update one or more fields, retaining others from existing data. Then notify the coordinator
    def _update(self, **kwargs: Any):
        self._data = replace(self._data, **kwargs)
        if self._callback is not None:
            self._callback(self._data)

    def _handle_distance_change(
        self, _: BleakGATTCharacteristic | None, data: bytearray
    ):
        self._logger.debug("Handle distance change %s", data)
        self._update(distance=int.from_bytes(data, "big"))

    def _handle_rotation_change(
        self, _: BleakGATTCharacteristic | None, data: bytearray
    ):
        self._logger.debug("Handle rotation change %s", data)
        self._update(rotation=int.from_bytes(data, "big"))

    async def _read_name(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_NAME_UUID)
        self._logger.debug("Read name %s", data)
        self._update(name=data.decode("utf-8").rstrip("\x00"))

    async def _read_distance(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_DISTANCE_UUID)
        self._logger.debug("Read distance %s", data)
        self._handle_distance_change(None, data)

    async def _read_rotation(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_ROTATION_UUID)
        self._logger.debug("Read rotation %s", data)
        self._handle_distance_change(None, data)

    async def _read_preset(self, preset_index: int):
        assert self._client is not None
        data1 = await self._client.read_gatt_char(CHAR_PRESET_UUIDS[preset_index])
        data2 = await self._client.read_gatt_char(CHAR_PRESET_NAMES_UUIDS[preset_index])
        data = data1 + data2
        self._logger.debug("Read preset for index %s data %s", preset_index, data)
        new_presets = dict(self._data.presets)
        new_presets[preset_index] = None
        if data[0] != 0:
            distance = max(0, min(int.from_bytes(data[1:3], "big"), 100))
            rotation = max(
                -100, min(int.from_bytes(data[3:5], "big", signed=True), 100)
            )
            name = data[5:].decode("utf-8").rstrip("\x00")
            new_presets[preset_index] = VogelsMotionMountPreset(
                index=preset_index,
                name=name,
                distance=distance,
                rotation=rotation,
            )
        self._update(presets=new_presets)

    async def _read_width(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_WIDTH_UUID)
        self._logger.debug("Read width %s", data)
        self._update(width=data[0])

    async def _read_freeze_preset(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_FREEZE_UUID)
        self._logger.debug("Read Freeze %s", data)
        self._update(freeze_preset_index=data[0])

    async def _read_automove(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_AUTOMOVE_UUID)
        self._logger.debug("Read automove %s", data)
        automove_id = int.from_bytes(data, "big")

        if automove_id in CHAR_AUTOMOVE_ON_OPTIONS:
            automove_types = [
                VogelsMotionMountAutoMoveType.Hdmi_1,
                VogelsMotionMountAutoMoveType.Hdmi_2,
                VogelsMotionMountAutoMoveType.Hdmi_3,
                VogelsMotionMountAutoMoveType.Hdmi_4,
                VogelsMotionMountAutoMoveType.Hdmi_5,
            ]
            self._update(
                automove_type=automove_types[
                    CHAR_AUTOMOVE_ON_OPTIONS.index(automove_id)
                ],
                automove_id=CHAR_AUTOMOVE_ON_OPTIONS.index(automove_id),
            )
        else:
            self._update(
                automove_type=VogelsMotionMountAutoMoveType.Off,
                automove_id=CHAR_AUTOMOVE_OFF_OPTIONS.index(automove_id),
            )

    async def _read_pin_settings(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_PIN_SETTINGS_UUID)
        self._logger.debug("Read Pin Settings %s", data)
        try:
            pin_setting = VogelsMotionMountPinSettings(int(data[0]))
            self._logger.debug("Read Pin Settings %s", pin_setting.name)
            self._update(pin_setting=pin_setting)
        except ValueError:
            self._logger.debug(
                "Read Pin Settings None (unknown value: %s)", int(data[0])
            )
            self._update(pin_setting=None)

    async def _read_multi_pin_features(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_MULTI_PIN_FEATURES_UUID)
        self._logger.debug("Read Multi Pin Features %s", data)
        value = data[0]
        self._update(
            multi_pin_features=MultiPinFeatures(
                change_presets=bool(value & (1 << 0)),
                change_name=bool(value & (1 << 1)),
                disable_channel=bool(value & (1 << 2)),
                change_tv_on_off_detection=bool(value & (1 << 3)),
                change_default_position=bool(value & (1 << 4)),
                start_calibration=bool(value & (1 << 7)),
            )
        )

    async def _read_version_ceb(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_VERSIONS_CEB_UUID)
        self._logger.debug("Read CEB Version %s", data)
        self._update(ceb_bl_version=".".join(str(b) for b in data))

    async def _read_version_mcp(self):
        assert self._client is not None
        data = await self._client.read_gatt_char(CHAR_VERSIONS_MCP_UUID)
        self._logger.debug("Read MCP Version %s", data)
        self._update(
            mcp_hw_version=".".join(str(b) for b in data[:3]),
            mcp_bl_version=".".join(str(b) for b in data[3:5]),
            mcp_fw_version=".".join(str(b) for b in data[5:7]),
        )

    # endregion
