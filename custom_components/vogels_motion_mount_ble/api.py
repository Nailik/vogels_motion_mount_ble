"""Bluetooth api to connect to Vogels MotionMount."""

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass, field, replace
from enum import Enum
import logging

from bleak import BleakClient, BLEDevice
from bleak.exc import BleakDeviceNotFoundError

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
    CHAR_NAME_UUID,
    CHAR_PIN_CHECK_UUID,
    CHAR_PIN_SETTINGS_UUID,
    CHAR_PRESET_UUID,
    CHAR_PRESET_UUIDS,
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

    name: str
    distance: int
    rotation: int


class VogelsMotionMountPinSettings(Enum):
    """Defines the possible pin settings."""

    Deactivated = 0x0C  # 12
    Single = 0x0D  # 13
    Multi = 0x0F  # 15


# TODO make not every field None but make only the whole dataclass noneable (evtl extract connected)
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
    automove_on: bool | None = None
    automove_id: int | None = None
    pin_setting: VogelsMotionMountPinSettings | None = None
    ceb_bl_version: str | None = None
    mcp_hw_version: str | None = None
    mcp_bl_version: str | None = None
    mcp_fw_version: str | None = None


class APIConnectionError(HomeAssistantError):
    """Exception class for unknown connection error."""


class APIConnectionDeviceNotFoundError(HomeAssistantError):
    """Exception class for connection error when device was not found."""


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

    # region Public api

    async def test_connection(self):
        """Test connection to the BLE device once using BleakClient and disconnects immediately."""
        _LOGGER.debug("Test connection to %s", self._mac)
        if not self._device:
            _LOGGER.error("Device not found with address %s", self._mac)
            raise APIConnectionDeviceNotFoundError("Device not found.")

        try:
            _LOGGER.debug(
                "Device found with address %s attempting to connect", self._mac
            )
            await self._connect()
            _LOGGER.debug("Connected to device %s", self._mac)
            await self.disconnect()
        except BleakDeviceNotFoundError as err:
            _LOGGER.error("Failed to connect to device %s", self._mac)
            raise APIConnectionDeviceNotFoundError("Device not found.") from err
        except Exception as err:
            _LOGGER.error("Failed to connect to device %s", self._mac)
            raise APIConnectionError("Error connecting to api.") from err

    async def disconnect(self):
        """Disconnect from the BLE Device."""
        if not self._client.is_connected:
            _LOGGER.debug(
                "Not connected to %s, no need to disconnect",
                self._mac,
            )
            return

        _LOGGER.debug("Diconnecting from %s", self._mac)
        await self._client.disconnect()
        _LOGGER.debug("Diconnected from %s", self._mac)

    async def unload(self):
        """Unload the api, disconnect and delete ble classes."""
        _LOGGER.debug("Unload from %s", self._mac)
        await self._client.disconnect()
        self._device = None
        self._client = None

    async def load_initial_data(self) -> None:
        """Load the initial data from the device."""
        while True:
            try:
                _LOGGER.debug(
                    "Initial data connection to device %s connecting", self._mac
                )
                await self.refreshData()
                break
            except ConfigEntryAuthFailed as err:
                _LOGGER.error(
                    "Authentication Exception while reading initial data %s", err
                )
                raise ConfigEntryAuthFailed from err
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Exception while reading initial data %s", err)
            await asyncio.sleep(15)

    async def refreshData(self):
        """Read data from BLE device, connects if necessary."""
        if self._client.is_connected:
            # Authenticate in order to make it visible that authentication does not work
            await self._authenticate()
            await self._read_current_data()
        else:
            # connect will automatically load data
            await self._connect()

    # region Actions API

    async def set_name(self, name: str):
        """Select a preset index to move the MotionMount to."""
        _LOGGER.debug("Change name to %s for %s", name, self._mac)
        newname = bytearray(name.encode("utf-8"))[:20].ljust(20, b"\x00")
        await self._connect(
            self._client.write_gatt_char,
            CHAR_NAME_UUID,
            newname,
            response=True,
        )
        self._update(name=newname)

    async def set_distance(self, distance: int):
        """Select a preset index to move the MotionMount to."""
        _LOGGER.debug("Set distance to %s for %s", distance, self._mac)
        await self._connect(
            self._client.write_gatt_char,
            CHAR_DISTANCE_UUID,
            int(distance).to_bytes(2, byteorder="big"),
            response=True,
        )

    async def set_rotation(self, rotation: int):
        """Select a preset index to move the MotionMount to."""
        _LOGGER.debug("Set rotation to %s for %s", rotation, self._mac)
        await self._connect(
            self._client.write_gatt_char,
            CHAR_ROTATION_UUID,
            int(rotation).to_bytes(2, byteorder="big", signed=True),
            response=True,
        )
        self._update(requested_rotation=rotation)

    async def set_preset(
        self,
        preset_index: int,
        name: str | None = None,
        distance: int | None = None,
        rotation: int | None = None,
    ):
        """Change data of a preset."""
        _LOGGER.debug(
            "Change preset %s to rotation %s, distance %s and name %s for %s",
            preset_index,
            name,
            distance,
            rotation,
            self._mac,
        )
        preset = self._data.presets[preset_index]

        new_name = name if name is not None else preset.name
        new_distance = distance if distance is not None else preset.distance
        new_rotation = rotation if rotation is not None else preset.rotation

        # TODO max length for name
        name_bytes = (new_name).encode("utf-8")
        distance_bytes = int(new_distance).to_bytes(2, byteorder="big")
        rotation_bytes = int(new_rotation).to_bytes(2, byteorder="big")

        data = b"\x01" + distance_bytes + rotation_bytes + name_bytes
        newpresets = dict(self._data.presets)

        newpresets[preset_index] = VogelsMotionMountPreset(
            name=new_name,
            distance=new_distance,
            rotation=new_rotation,
        )

        await self._connect(
            self._client.write_gatt_char,
            CHAR_PRESET_UUIDS[preset_index],
            data[:20].ljust(20, b"\x00"),
            response=True,
        )
        self._update(presets=newpresets)

    async def delete_preset(self, preset_index: int):
        """Delete a preset by index to move the MotionMount to."""
        _LOGGER.debug("Delete preset %s for %s", preset_index, self._mac)
        newpresets = dict(self._data.presets)
        newpresets[preset_index] = None
        await self._connect(
            self._client.write_gatt_char,
            CHAR_PRESET_UUIDS[preset_index],
            bytes(0x01).ljust(20, b"\x00"),
            response=True,
        )
        self._update(presets=newpresets)

    async def select_preset(self, preset_index: int):
        """Select a preset index to move the MotionMount to."""
        _LOGGER.debug("Select preset %s for %s", preset_index, self._mac)
        await self._connect(
            self._client.write_gatt_char,
            CHAR_PRESET_UUID,
            bytes([preset_index]),
            response=True,
        )

    async def set_width(self, width: int):
        """Select a preset index to move the MotionMount to."""
        _LOGGER.debug("Set width %s for %s", width, self._mac)
        await self._connect(
            self._client.write_gatt_char, CHAR_WIDTH_UUID, bytes([width]), response=True
        )
        self._update(width=width)

    async def set_automove(self, id: int | None):
        """Select a automove option where None is off."""
        _LOGGER.debug("Set automove to %s for %s", id, self._mac)
        data: int
        on: bool
        new_id: int
        if id:
            data = CHAR_AUTOMOVE_ON_OPTIONS[id]
            on = True
            new_id = id
        else:
            data = (
                CHAR_AUTOMOVE_OFF_OPTIONS[self._data.automove_id]
                if self._data.automove_id
                else 0
            )
            on = False
            new_id = self._data.automove_id

        await self._connect(
            self._client.write_gatt_char,
            CHAR_AUTOMOVE_UUID,
            int(data).to_bytes(2, byteorder="big"),
            response=True,
        )
        self._update(
            automove_on=on,
            automove_id=new_id,
        )

    async def set_authorised_user_pin(self, pin: str):
        """Set 4 digit pin for authorised users."""
        _LOGGER.debug("Set authorized user pin to %s for %s", pin, self._mac)

        if len(pin) == 4 and pin.isdigit():
            data = int(pin).to_bytes(2, byteorder="little")
            await self._connect(
                self._client.write_gatt_char,
                CHAR_PIN_SETTINGS_UUID,
                data,
                response=True,
            )
        else:
            _LOGGER.warning("Invalid change set_supervisior_pin to %s", pin)

    async def set_supervisior_pin(self, pin: str):
        """Set 4 digit pin for supervisior."""
        _LOGGER.debug("Set superivisor pin to %s for %s", pin, self._mac)

        if len(pin) == 4 and pin.isdigit():
            data = int(pin).to_bytes(2, byteorder="little")
            await self._connect(
                self._client.write_gatt_char,
                CHAR_PIN_SETTINGS_UUID,
                data,
                response=True,
            )
        else:
            _LOGGER.warning("Invalid change set_supervisior_pin to %s", pin)

    async def set_freeze(self, preset_index: int):
        """Set preset that is used for auto move freeze position."""
        _LOGGER.debug("Set freeze preset index to %s for %s", preset_index, self._mac)

        await self._connect(
            self._client.write_gatt_char,
            CHAR_FREEZE_UUID,
            bytes([preset_index]),
            response=True,
        )
        self._update(freeze_preset_index=preset_index)

    # endregion
    # endregion
    # region Private functions

    async def _connect(
        self,
        connected: Callable[[], Awaitable[None]] = None,
        *args,
        **kwargs,
    ):
        """Connect and load initial data, skips and loads data if already connected."""
        _LOGGER.debug("Connect to %s", self._mac)

        if self._client.is_connected:
            should_read_data = False
            _LOGGER.debug(
                "Already connected to %s, no need to connect again",
                self._mac,
            )
        else:
            should_read_data = True
            _LOGGER.debug("Connecting to %s", self._mac)
            await self._client.connect(timeout=120)
            _LOGGER.debug("Connected to %s!", self._mac)

        self._update(connected=self._client.is_connected)

        await self._authenticate()

        if connected is not None:
            # calls callback before loading data in order to run command with less delay
            await connected(*args, **kwargs)

        if should_read_data:
            # only read data and setup notifications if this was a new connection
            await self._setup_notifications()
            await self._read_current_data()

    async def _authenticate(self):
        _LOGGER.debug("Authenticate to %s", self._mac)

        # TODO allow different authentication types (different settings required different pin)
        # TODO evaluate result of action if authenticated proberly?
        # TODO handle timeout (seems to start at 127 and then count down to zero?)
        # Authenticate if necessary, raises APIAuthenticationError if not successful.
        _raw_auth = await self._client.read_gatt_char(CHAR_PIN_CHECK_UUID)
        _pin_required = int.from_bytes(_raw_auth, "big")

        if _raw_auth.startswith(b"\x80"):
            _LOGGER.debug(
                "No authentication required %s (raw %s) or already authenticated",
                _pin_required,
                _raw_auth,
            )
            return

        _LOGGER.debug(
            "Authentication required %s (raw %s) sending pin %s",
            _pin_required,
            _raw_auth,
            self._pin,
        )
        if self._pin is None:
            raise ConfigEntryAuthFailed

        await self._client.write_gatt_char(
            CHAR_AUTHENTICATE_UUID, int(self._pin).to_bytes(2, byteorder="little")
        )

        for attempt in range(4):
            _raw_auth = await self._client.read_gatt_char(CHAR_PIN_CHECK_UUID)
            _pin_required = int.from_bytes(_raw_auth, "big")
            if _raw_auth.startswith(b"\x80"):
                _LOGGER.debug(
                    "Authentication successful %s (raw %s)", _pin_required, _raw_auth
                )
                return
            _LOGGER.debug(
                "Not authenticated yet %s (raw %s), retry %s",
                _pin_required,
                _raw_auth,
                attempt,
            )
            if attempt < 3:
                await asyncio.sleep(0.1)

        raise ConfigEntryAuthFailed

    def _handle_disconnect(self, _):
        # Update state when client disconnects.
        _LOGGER.debug("Device %s disconnected!", self._mac)
        self._update(connected=self._client.is_connected)

    async def _setup_notifications(self):
        """Notifications in order to get udpates from device via ble notify."""
        _LOGGER.debug("Setup notifications for device %s", self._mac)
        await self._client.start_notify(
            char_specifier=CHAR_DISTANCE_UUID,
            callback=self._handle_distance_change,
        )
        await self._client.start_notify(
            char_specifier=CHAR_ROTATION_UUID,
            callback=self._handle_rotation_change,
        )

    async def _read_current_data(self):
        """Read all data from device."""
        _LOGGER.debug("Read current data from device %s", self._mac)
        self._handle_name_change(await self._client.read_gatt_char(CHAR_NAME_UUID))
        self._handle_distance_change(
            None, await self._client.read_gatt_char(CHAR_DISTANCE_UUID)
        )
        self._handle_rotation_change(
            None, await self._client.read_gatt_char(CHAR_ROTATION_UUID)
        )
        for preset_index in range(7):
            self._handle_preset_change(
                preset_index + 1,
                await self._client.read_gatt_char(CHAR_PRESET_UUIDS[preset_index]),
            )
        self._handle_width_change(await self._client.read_gatt_char(CHAR_WIDTH_UUID))
        self._handle_freeze_preset_change(
            await self._client.read_gatt_char(CHAR_FREEZE_UUID)
        )
        self._handle_automove_change(
            await self._client.read_gatt_char(CHAR_AUTOMOVE_UUID)
        )
        self._handle_version_ceb_change(
            await self._client.read_gatt_char(CHAR_VERSIONS_CEB_UUID)
        )
        self._handle_version_mcp_change(
            await self._client.read_gatt_char(CHAR_VERSIONS_MCP_UUID)
        )

    def _update(self, **kwargs):
        """Update one or more fields, retaining others from existing data. Then notify the coordinator."""
        self._data = replace(self._data, **kwargs)
        self._callback(self._data)

    def _handle_name_change(self, data: bytearray):
        _LOGGER.debug("Handle name change %s", data)
        self._update(name=data.decode("utf-8").rstrip("\x00"))

    def _handle_distance_change(self, _, data: bytearray):
        _LOGGER.debug("Handle distance change %s", data)
        self._update(distance=int.from_bytes(data, "big"))

    def _handle_rotation_change(self, _, data: bytearray):
        _LOGGER.debug("Handle rotation change %s", data)
        self._update(rotation=int.from_bytes(data, "big"))

    def _handle_preset_change(self, preset_index, data: bytearray):
        _LOGGER.debug("Handle preset change for id %s data %s", preset_index, data)

        new_presets = dict(self._data.presets)
        new_presets[preset_index] = None
        # check if data is empty, if so then preset doesn't exist
        if data[0] != 0:
            # Preset IDs are 1-based because 0 is the default preset
            distance = int.from_bytes(data[1:3], "big")
            rotation = int.from_bytes(data[3:5], "big")
            name = data[5:].decode("utf-8").rstrip("\x00")
            new_presets[preset_index] = VogelsMotionMountPreset(
                name=name,
                distance=distance,
                rotation=rotation,
            )

        self._update(presets=new_presets)

    def _handle_width_change(self, data: bytearray):
        _LOGGER.debug("Handle width change %s", data)

        self._update(width=data[0])

    def _handle_freeze_preset_change(self, data):
        _LOGGER.debug("Handle Freeze preset change %s", data)
        self._update(
            freeze_preset_index=data[0],
        )

    def _handle_automove_change(self, data: bytearray):
        automove_id = int.from_bytes(data, "big")
        _LOGGER.debug("Handle automove change %s", automove_id)

        if automove_id in CHAR_AUTOMOVE_ON_OPTIONS:
            self._update(
                automove_on=True,
                automove_id=CHAR_AUTOMOVE_ON_OPTIONS.index(automove_id),
            )
        else:
            self._update(
                automove_on=False,
                automove_id=CHAR_AUTOMOVE_OFF_OPTIONS.index(automove_id),
            )

    def _handle_pin_settings_change(self, data):
        # data is split across 2 different data sets
        _LOGGER.debug("Handle Pin Settings change %s", data)

        if data == VogelsMotionMountPinSettings.Deactivated:
            self._update(
                pin_setting=VogelsMotionMountPinSettings.Deactivated,
            )
        elif data == VogelsMotionMountPinSettings.Single:
            self._update(
                pin_setting=VogelsMotionMountPinSettings.Single,
            )
        elif data == VogelsMotionMountPinSettings.Multi:
            self._update(
                pin_setting=VogelsMotionMountPinSettings.Multi,
            )
        else:
            self._update(
                pin_setting=None,
            )

    def _handle_version_ceb_change(self, data):
        # data is split across 2 different data sets
        _LOGGER.debug("Handle CEB Version change %s", data)

        self._update(
            ceb_bl_version=".".join(str(b) for b in data),
        )

    def _handle_version_mcp_change(self, data):
        # data is split across 2 different data sets
        _LOGGER.debug("Handle MCP Version change %s", data)
        self._update(
            mcp_hw_version=".".join(str(b) for b in data[:3]),
            mcp_bl_version=".".join(str(b) for b in data[3:5]),
            mcp_fw_version=".".join(str(b) for b in data[5:7]),
        )

    # endregion
