"""Bluetooth api to connect to Vogels MotionMount."""

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass, field, replace
from enum import Enum
import logging

from bleak import BleakClient, BLEDevice
from bleak.exc import BleakDeviceNotFoundError
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import Callable, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError

from .const import (
    CHAR_AUTHENTICATE_UUID,
    CHAR_AUTOMOVE_OFF_OPTIONS,
    CHAR_AUTOMOVE_ON_OPTIONS,
    CHAR_AUTOMOVE_UUID,
    CHAR_DISTANCE_UUID,
    CHAR_FREEZE_UUID,
    CHAR_MULTI_PIN_FEATURES_UUID,
    CHAR_NAME_UUID,
    CHAR_PIN_CHECK_UUID,
    CHAR_CHANGE_PIN_UUID,
    CHAR_PIN_SETTINGS_UUID,
    CHAR_PRESET_UUID,
    CHAR_PRESET_UUIDS,
    CHAR_PRESET_NAMES_UUIDS,
    CHAR_ROTATION_UUID,
    CHAR_VERSIONS_CEB_UUID,
    CHAR_VERSIONS_MCP_UUID,
    CHAR_WIDTH_UUID,
)

_LOGGER = logging.getLogger(__name__)

# region Public data classes


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

    Wrong = -2
    Missing = -1
    Control = 0
    Full = 1

class VogelsMotionMountAutoMoveType(Enum):
    """Defines the authentication options."""

    Off = "off"
    Hdmi_1 = "hdmi_1"
    Hdmi_2 = "hdmi_2"
    Hdmi_3 = "hdmi_3"
    Hdmi_4 = "hdmi_4"
    Hdmi_5 = "hdmi_5"

class VogelsMotionActionType(Enum):
    """Defines the possible actions."""

    Control = 0 # control the device
    Settings = 1 # change settings


@dataclass
class MultiPinFeatures:
    """Holds the information what the pin is verified for."""

    change_presets: bool
    change_name: bool
    disable_channel: bool
    change_tv_on_off_detection: bool
    change_default_position: bool
    start_calibration: bool


@dataclass
class VogelsMotionMountData:
    """Holds the data of the device."""

    connected: bool = False
    name: str | None = None
    distance: int | None = None
    rotation: int | None = None
    requested_distance: int | None = None
    requested_rotation: int | None = None
    presets: dict[int, VogelsMotionMountPreset | None] = field(default_factory=dict)
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
    pin_type: VogelsMotionMountPinType | None = None
    auth_type: VogelsMotionMountAuthenticationType | None = None


class APIConnectionError(HomeAssistantError):
    """Exception class for unknown connection error."""


class APIConnectionDeviceNotFoundError(HomeAssistantError):
    """Exception class for connection error when device was not found."""


class APIAuthenticationError(HomeAssistantError):
    """Exception class if user is not authorized to do this action."""


class APISettingsChangeNotStoredError(HomeAssistantError):
    """Exception class if changed settings are not saved on vogels motion mount."""

class APISettingsChangeInvalidInputError(HomeAssistantError):
    """Exception class if changed settings input data is invalid."""


# endregion


class API:
    """Bluetooth API."""

    def __init__(
        self,
        hass: HomeAssistant,
        mac: str,
        pin: str | None,
        callback: Callable[[VogelsMotionMountData], None],
    ) -> None:
        """Set up the default data."""
        self._logger = logging.getLogger(f"{__name__}.{mac}")
        self._logger.debug("Setup bluetooth api with mac %s and pin %s", mac, pin)
        self._hass = hass
        self._mac = mac
        self._pin = pin
        self._callback = callback
        self._data = VogelsMotionMountData(connected=False)
        self._device: BLEDevice = bluetooth.async_ble_device_from_address(
            self._hass, self._mac, connectable=True
        )
        self._client: BleakClient = BleakClient(
            self._device, disconnected_callback=self._handle_disconnect, timeout=120
        )
        self._load_task = None

    # region Public api

    async def test_connection(self):
        """Test connection to the BLE device once using BleakClient and disconnects immediately."""
        self._logger.debug("Test connection")
        try:
            # make sure we are disconnected before testing connection otherwise authentication might not be tested
            await self.disconnect()
            self._logger.debug("Device found attempting to connect")
            self._client = await establish_connection(self._device, self._device.name)
            await self._authenticate()
            self._logger.debug("Connected")
            await self.disconnect()
        except BleakDeviceNotFoundError as err:
            self._logger.error("Failed to connect")
            raise APIConnectionDeviceNotFoundError("Device not found.") from err
        except Exception as err:
            self._logger.error("Failed to connect")
            raise APIConnectionError("Error connecting to api.") from err

    async def disconnect(self):
        """Disconnect from the BLE Device."""
        self._logger.debug("Diconnecting")
        await self._client.disconnect()
        self._logger.debug("Diconnected!")

    async def unload(self):
        """Unload the api, disconnect and delete ble classes."""
        self._logger.debug("Unload")
        await self.disconnect()
        self._device = None
        self._client = None
    
    async def refreshData(self):
        """Read data from BLE device, connects if necessary."""
        if self._client.is_connected:
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

        if distance in range(-100,100):
            raise APISettingsChangeInvalidInputError(f"Invalid distance {distance} must be in range(-100,100).")
        
        await self._connect(
            VogelsMotionActionType.Control,
            self._client.write_gatt_char,
            CHAR_DISTANCE_UUID,
            int(distance).to_bytes(2, byteorder="big"),
            response=True,
        )
        self._update(requested_distance=distance)

    async def set_rotation(self, rotation: int):
        """Set the rotation move the MotionMount to."""
        self._logger.debug("Set rotation to %s", rotation)
        
        if rotation in range(-100,100):
            raise APISettingsChangeInvalidInputError(f"Invalid rotation {rotation} must be in range(-100,100).")
        
        await self._connect(
            VogelsMotionActionType.Control,
            self._client.write_gatt_char,
            CHAR_ROTATION_UUID,
            int(rotation).to_bytes(2, byteorder="big", signed=True),
            response=True,
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
            VogelsMotionActionType.Control,
            self._client.write_gatt_char,
            CHAR_PRESET_UUID,
            bytes([0]),
            response=True,
        )

    async def select_preset(self, preset_index: int):
        """Select a preset index to move the MotionMount to."""
        self._logger.debug("Select preset %s", preset_index)

        if preset_index in range(7) and self._data.presets[preset_index] is not None:
            raise APISettingsChangeInvalidInputError(f"Invalid preset index {preset_index} should be in range(7).")
        
        if self._data.presets[preset_index] is None:
            raise APISettingsChangeInvalidInputError(f"Preset at index {preset_index} doesn't exist.")
        
        await self._connect(
            VogelsMotionActionType.Control,
            self._client.write_gatt_char,
            CHAR_PRESET_UUID,
            bytes(
                [preset_index + 1]
            ),  # Preset IDs are 1-based because 0 is the default preset
            response=True,
        )
    
    # endregion
    # region Settings

    async def set_name(self, name: str):
        """Set the bluetooth name for the deice."""
        self._logger.debug("Change name to %s", name)
        if len(name) > 20:
            raise APISettingsChangeInvalidInputError(f"Name {name} too long, max length is 20 characters.")

        newname = bytearray(name.encode("utf-8"))[:20].ljust(20, b"\x00")
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_NAME_UUID,
            newname,
            response=True,
        )
        await self._read_name()
        if self._data.name != name:
            raise APISettingsChangeNotStoredError(
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
        preset = self._data.presets[preset_index]

        new_name: str = name if name is not None else preset.name if preset is not None else f"{preset_index}"

        if len(new_name) > 32:
            raise APISettingsChangeInvalidInputError(f"Name {name} too long, max length is 32 characters.")
        
        new_distance = distance if distance is not None else preset.distance if preset is not None else 0
        new_rotation = rotation if rotation is not None else preset.rotation if preset is not None else 0

        distance_bytes = int(new_distance).to_bytes(2, byteorder="big")
        rotation_bytes = int(new_rotation).to_bytes(2, byteorder="big", signed=True)
        name_bytes = new_name.encode("utf-8")

        data = b"\x01" + distance_bytes + rotation_bytes + name_bytes
      
        #write first 20 bytes, distance, rotation and beginning of name
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_PRESET_UUIDS[preset_index],
            data[:20].ljust(20, b"\x00"),
            response=True,
        )
        #write rest of name
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_PRESET_NAMES_UUIDS[preset_index],
            data[20:].ljust(17, b"\x00"),
            response=True,
        )

        await self._read_preset(preset_index)
        expected_data = VogelsMotionMountPreset(
            index=preset_index,
            name=new_name,
            distance=new_distance,
            rotation=new_rotation,
        )
        if self._data.presets[preset_index] != expected_data:
            raise APISettingsChangeNotStoredError(
                f"Preset change not saved on device. Expected {expected_data} actual {self._data.presets[preset_index]}."
            )

    async def delete_preset(self, preset_index: int):
        """Delete a preset by index to move the MotionMount to."""
        self._logger.debug("Delete preset %s", preset_index)
        
        if preset_index in range(7) and self._data.presets[preset_index] is not None:
            raise APISettingsChangeInvalidInputError(f"Invalid preset index {preset_index} should be in range(7).")
        
        if self._data.presets[preset_index] is None:
            raise APISettingsChangeInvalidInputError(f"Preset at index {preset_index} doesn't exist.")
    
        newpresets = dict(self._data.presets)
        newpresets[preset_index] = None
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_PRESET_UUIDS[preset_index],
            bytes(0x01).ljust(20, b"\x00"),
            response=True,
        )
        await self._read_preset(preset_index)
        if self._data.presets[preset_index] is not None:
            raise APISettingsChangeNotStoredError(f"Preset delete not saved on device. Expected None actual {self._data.presets[preset_index]}.")

    async def set_width(self, width: int):
        """Select a preset index to move the MotionMount to."""
        self._logger.debug("Set width %s", width)
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char, 
            CHAR_WIDTH_UUID, 
            bytes([width]), 
            response=True,
        )
        await self._read_width()
        if self._data.width != width:
            raise APISettingsChangeNotStoredError(f"Width data not saved on device. Expected {width} actual {self._data.width}.")

    async def set_automove(self, id: str):
        """Select a automove option where None is off."""
        self._logger.debug("Set automove to %s", id)

        try:
            automove_type = VogelsMotionMountAutoMoveType(id)
        except ValueError:
            raise APISettingsChangeInvalidInputError(f"AutoMove type {id} does not exist, must be any of \"off\", \"hdmi_1\", \"hdmi_2\", \"hdmi_3\", \"hdmi_4\", \"hdmi_5\".")
        
        if automove_type == VogelsMotionMountAutoMoveType.Off:
            new_id = CHAR_AUTOMOVE_OFF_OPTIONS[self._data.automove_id if self._data.automove_id is not None else 0]
        else:
            automove_types = [
                VogelsMotionMountAutoMoveType.Hdmi_1, 
                VogelsMotionMountAutoMoveType.Hdmi_2, 
                VogelsMotionMountAutoMoveType.Hdmi_3, 
                VogelsMotionMountAutoMoveType.Hdmi_4, 
                VogelsMotionMountAutoMoveType.Hdmi_5
            ]
            new_id = CHAR_AUTOMOVE_ON_OPTIONS[automove_types.index(automove_type)]

        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_AUTOMOVE_UUID,
            int(new_id).to_bytes(2, byteorder="big"),
            response=True,
        )
        await self._read_automove()
        if self._data.automove_id != new_id or self._data.automove_type != automove_type:
            raise APISettingsChangeNotStoredError(f"Automove data not saved on device. Expected id {new_id} actual {self._data.automove_id}, expected type {automove_type} actual {self._data.automove_type}.")

    async def set_authorised_user_pin(self, pin: str):
        """Set 4 digit pin for authorised users."""
        self._logger.debug("Set authorized user pin to %ss", pin)
        remove = pin == "0000"

        if remove and self._data.pin_setting == VogelsMotionMountPinSettings.Multi:
            raise APISettingsChangeInvalidInputError("Authorised user pin cannot be deactivated when supervisior pin is set.")
        
        if len(pin) != 4:
            raise APISettingsChangeInvalidInputError("Authorised user pin is too long, max length 4 digits.")
        
        if not pin.isdigit():
            raise APISettingsChangeInvalidInputError("Authorised user pin contains non digit characters.")
        
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_CHANGE_PIN_UUID,
             int(pin).to_bytes(2, byteorder="little"),
            response=True,
        )
        await self._read_pin_settings()

        if remove and self._data.pin_setting != VogelsMotionMountPinSettings.Deactivated:
            raise APISettingsChangeNotStoredError(f"Authorised user pin was not set removed. Expected pin settings {VogelsMotionMountPinSettings.Deactivated} actual  {self._data.pin_setting}.")
        
        if not remove and self._data.pin_setting == VogelsMotionMountPinSettings.Deactivated:
            raise APISettingsChangeNotStoredError(f"Authorised user pin was not set removed. Expected pin settings {VogelsMotionMountPinSettings.Single} or {VogelsMotionMountPinSettings.Multi} actual  {self._data.pin_setting}.")


    async def set_supervisior_pin(self, pin: str):
        """Set 4 digit pin for supervisior."""
        self._logger.debug("Set supervisior pin to %ss", pin)
        remove = pin == "0000"

        if remove and self._data.pin_setting == VogelsMotionMountPinSettings.Single:
            raise APISettingsChangeInvalidInputError("Supervisior pin cannot be deactivated when supervisior pin is not set.")
        
        if self._data.pin_setting == VogelsMotionMountPinSettings.Deactivated:
            raise APISettingsChangeInvalidInputError("Supervisior pin cannot be set when authorized user pin is not set.")
        
        if len(pin) != 4:
            raise APISettingsChangeInvalidInputError("Supervisior pin is too long, max length 4 digits.")
        
        if not pin.isdigit():
            raise APISettingsChangeInvalidInputError("Supervisior pin contains non digit characters.")
        
        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_CHANGE_PIN_UUID,
             int(pin).to_bytes(2, byteorder="little"),
            response=True,
        )
        await self._read_pin_settings()

        if remove and self._data.pin_setting != VogelsMotionMountPinSettings.Single:
            raise APISettingsChangeNotStoredError(f"Authorised user pin was not set removed. Expected pin settings {VogelsMotionMountPinSettings.Single} actual {self._data.pin_setting}.")
        
        if not remove and self._data.pin_setting != VogelsMotionMountPinSettings.Multi:
            raise APISettingsChangeNotStoredError(f"Supervisior pin was not set. Expected pin settings {VogelsMotionMountPinSettings.Multi} actual  {self._data.pin_setting}.")

    async def set_freeze(self, preset_index: int):
        """Set preset that is used for auto move freeze position."""
        self._logger.debug("Set freeze preset index to %s", preset_index)

        if preset_index in range(7) and self._data.presets[preset_index] is not None:
            raise APISettingsChangeInvalidInputError(f"Invalid preset index {preset_index} should be in range(7).")
        
        if self._data.presets[preset_index] is None:
            raise APISettingsChangeInvalidInputError(f"Preset at index {preset_index} doesn't exist.")

        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_FREEZE_UUID,
            bytes([preset_index]),
            response=True,
        )
        await self._read_freeze_preset()
        if self._data.freeze_preset_index != preset_index:
            raise APISettingsChangeNotStoredError(f"Freeze preset data not saved on device. Expected {preset_index} actual {self._data.freeze_preset_index}.")

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
            change_presets = False,
            change_name = False,
            disable_channel = False,
            change_tv_on_off_detection = False,
            change_default_position= False,
            start_calibration= False,
        )

        new_change_presets = change_presets or multi_pin_features.change_presets
        new_change_name = change_name or multi_pin_features.change_name
        new_disable_channel = disable_channel or multi_pin_features.disable_channel
        new_change_tv_on_off_detection = change_tv_on_off_detection or multi_pin_features.change_tv_on_off_detection
        new_change_default_position = change_default_position or multi_pin_features.change_default_position
        new_start_calibration = start_calibration or multi_pin_features.start_calibration

        value = 0
        value |= int(new_change_presets) << 0
        value |= int(new_change_name) << 1
        value |= int(new_disable_channel) << 2
        value |= int(new_change_tv_on_off_detection) << 3
        value |= int(new_change_default_position) << 4
        value |= int(new_start_calibration) << 7

        await self._connect(
            VogelsMotionActionType.Settings,
            self._client.write_gatt_char,
            CHAR_PIN_SETTINGS_UUID,
            bytes([value]),
            response=True,
        )
        self._read_multi_pin_features()
        new_multi_pin_features = MultiPinFeatures(
            change_presets=new_change_presets,
            change_name=new_change_name,
            disable_channel=new_disable_channel,
            change_tv_on_off_detection=new_change_tv_on_off_detection,
            change_default_position=new_change_default_position,
            start_calibration=new_start_calibration,
        )
        if self._data.multi_pin_features != new_multi_pin_features:
            raise APISettingsChangeNotStoredError(f"Multi pin features data not saved on device. Expected {new_multi_pin_features} actual {self._data.multi_pin_features}.")

    # endregion
    # endregion
    # region Private functions

    # connect and load data if new connection
    # checks authentication for this action type else raises an APIAuthenticationError error
    async def _connect(
        self,
        type: VogelsMotionActionType | None = None,
        connected: Callable[[], Awaitable[None]] = None,
        *args,
        **kwargs,
    ):
        self._logger.debug("Connect")

        if self._client.is_connected:
            should_read_data = False
            self._logger.debug("Already connected, no need to connect again")
        else:
            should_read_data = True
            self._logger.debug("Connecting")
            self._client = await establish_connection(self._device, self._device.name)
            self._logger.debug("Connected!")

        self._update(connected=self._client.is_connected)

        await self._authenticate(type)

        if connected is not None:
            # calls callback before loading data in order to run command with less delay
            await connected(*args, **kwargs)

        if should_read_data:
            # only read data and setup notifications if this was a new connection
            await self._setup_notifications()
            await self._read_current_data()

    # encodes the pin depending on type
    def _encode_pin(self, mode: VogelsMotionMountPinType) -> bytes:
        """Encode a PIN into 2-byte sequence for API.

        mode = "auth"   -> direct little-endian
        mode = "change" -> little-endian, high byte + 0x40
        """
        # Convert to little-endian bytes
        pin = int(self._pin)
        low = pin & 0xFF
        high = (pin >> 8) & 0xFF

        if mode == VogelsMotionMountPinType.Supervisior:
            high = (high + 0x40) & 0xFF  # add offset, wrap if >255

        return bytes([low, high])

    # check if authentication is full or only control or none at all
    async def _check_authentication(self) -> bool:
        _auth_info = await self._client.read_gatt_char(CHAR_PIN_CHECK_UUID)
        if _auth_info.startswith(b"\x80\x80"):
            self._update(auth_type=VogelsMotionMountAuthenticationType.Full)
        elif _auth_info.startswith(b"\x80"):
            self._update(auth_type=VogelsMotionMountAuthenticationType.Control)
        else:
            return False
        return True

    # authenticate as a specific pin type
    # stores the pin_type if successful
    async def _authenticate_as(self, type: VogelsMotionMountPinType) -> bool:
        self._logger.debug("_authenticate_as %s", type)
        await self._client.write_gatt_char(
            CHAR_AUTHENTICATE_UUID, self._encode_pin(type)
        )
        for attempt in range(4):
            if await self._check_authentication():
                self._update(pin_type=type)
                self._logger.debug("_authenticate_as %s success", type)
                return True
            if attempt < 3:
                await asyncio.sleep(0.1)
        self._logger.debug("_authenticate_as %s fail", type)
        return False

    # authenticate the user for this action type
    # if already authenticated only checks for correct type
    # else tries to authenticate for supervisior first and then for authorized user
    async def _authenticate(self, type: VogelsMotionActionType | None = None):
        self._logger.debug("Authenticate")

        if await self._check_authentication():
            self._logger.debug("already authenticated!")
            if self._data.auth_type == VogelsMotionMountAuthenticationType.Control and type == VogelsMotionActionType.Settings:
                raise APIAuthenticationError("Not authenticated for settings action.")
            return

        # authentication required but no pin set
        if self._pin is None:
            self._update(auth_type=VogelsMotionMountAuthenticationType.Missing)
            raise ConfigEntryAuthFailed

        authentication_types = (
            [
                VogelsMotionMountPinType.Authorized_user,
                VogelsMotionMountPinType.Supervisior,
            ]
            if self._data.pin_type == VogelsMotionMountPinType.Authorized_user
            else [
                VogelsMotionMountPinType.Supervisior,
                VogelsMotionMountPinType.Authorized_user,
            ]
        )

        for type in authentication_types:
            if await self._authenticate_as(type=type):
                if type == VogelsMotionMountAuthenticationType.Control and type == VogelsMotionActionType.Settings:
                    raise APIAuthenticationError("Not authenticated for settings action.")
                return

        self._update(auth_type=VogelsMotionMountAuthenticationType.Wrong)
        raise ConfigEntryAuthFailed

    # disconnect from the client
    def _handle_disconnect(self, _):
        self._logger.debug("Device disconnected!")
        self._update(connected=self._client.is_connected)

    # Notifications in order to get udpates from device via ble notify.
    async def _setup_notifications(self):
        self._logger.debug("Setup notifications")
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
    def _update(self, **kwargs):
        self._data = replace(self._data, **kwargs)
        self._callback(self._data)

    def _handle_distance_change(self, _, data: bytearray):
        self._logger.debug("Handle distance change %s", data)
        self._update(distance=int.from_bytes(data, "big"))

    def _handle_rotation_change(self, _, data: bytearray):
        self._logger.debug("Handle rotation change %s", data)
        self._update(rotation=int.from_bytes(data, "big"))

    async def _read_name(self):
        data = await self._client.read_gatt_char(CHAR_NAME_UUID)
        self._logger.debug("Read name %s", data)
        self._update(name=data.decode("utf-8").rstrip("\x00"))

    async def _read_distance(self):
        data = await self._client.read_gatt_char(CHAR_DISTANCE_UUID)
        self._logger.debug("Read distance %s", data)
        self._handle_distance_change(None, data)

    async def _read_rotation(self):
        data = await self._client.read_gatt_char(CHAR_ROTATION_UUID)
        self._logger.debug("Read rotation %s", data)
        self._handle_distance_change(None, data)

    async def _read_preset(self, preset_index):
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
        data = await self._client.read_gatt_char(CHAR_WIDTH_UUID)
        self._logger.debug("Read width %s", data)
        self._update(width=data[0])

    async def _read_freeze_preset(self):
        data = await self._client.read_gatt_char(CHAR_FREEZE_UUID)
        self._logger.debug("Read Freeze %s", data)
        self._update(freeze_preset_index=data[0])

    async def _read_automove(self):
        data = await self._client.read_gatt_char(CHAR_AUTOMOVE_UUID)
        self._logger.debug("Read automove %s", data)
        automove_id = int.from_bytes(data, "big")

        if automove_id in CHAR_AUTOMOVE_ON_OPTIONS:
            automove_types = [
                VogelsMotionMountAutoMoveType.Hdmi_1, 
                VogelsMotionMountAutoMoveType.Hdmi_2, 
                VogelsMotionMountAutoMoveType.Hdmi_3, 
                VogelsMotionMountAutoMoveType.Hdmi_4, 
                VogelsMotionMountAutoMoveType.Hdmi_5
            ]
            self._update(
                automove_type=automove_types[automove_id],
                automove_id=CHAR_AUTOMOVE_ON_OPTIONS.index(automove_id),
            )
        else:
            self._update(
                automove_type=VogelsMotionMountAutoMoveType.Off,
                automove_id=CHAR_AUTOMOVE_OFF_OPTIONS.index(automove_id),
            )

    async def _read_pin_settings(self):
        data = await self._client.read_gatt_char(CHAR_PIN_SETTINGS_UUID)
        self._logger.debug("Read Pin Settings %s", data)
        try:
            pin_setting = VogelsMotionMountPinSettings(int(data[0]))
            self._logger.debug("Read Pin Settings %s", pin_setting.name)
            self._update(pin_setting=pin_setting)
        except ValueError:
            self._logger.debug("Read Pin Settings None (unknown value: %s)", int(data[0]))
            self._update(pin_setting=None)

    async def _read_multi_pin_features(self):
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
        data = await self._client.read_gatt_char(CHAR_VERSIONS_CEB_UUID)
        self._logger.debug("Read CEB Version %s", data)
        self._update(ceb_bl_version=".".join(str(b) for b in data))

    async def _read_version_mcp(self):
        data = await self._client.read_gatt_char(CHAR_VERSIONS_MCP_UUID)
        self._logger.debug("Read MCP Version %s", data)
        self._update(
            mcp_hw_version=".".join(str(b) for b in data[:3]),
            mcp_bl_version=".".join(str(b) for b in data[3:5]),
            mcp_fw_version=".".join(str(b) for b in data[5:7]),
        )

    # endregion
