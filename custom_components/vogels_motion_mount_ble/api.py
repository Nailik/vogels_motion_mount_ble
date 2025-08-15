"""Bluetooth api to connect to Vogels MotionMount and send and recieve data."""

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass, field, replace
import logging

from bleak import BleakClient, BLEDevice
from bleak.exc import BleakDeviceNotFoundError

from homeassistant.components import bluetooth
from homeassistant.core import Callable, HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CHAR_AUTOMOVE_OFF_OPTIONS,
    CHAR_AUTOMOVE_ON_OPTIONS,
    CHAR_AUTOMOVE_UUID,
    CHAR_DISTANCE_UUID,
    CHAR_NAME_UUID,
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

    id: int
    name: str
    distance: int
    rotation: int


@dataclass
class VogelsMotionMountData:
    """Holds the data of the device."""

    connected: bool = False
    distance: int | None = None
    rotation: int | None = None
    requested_distance: int | None = None
    requested_rotation: int | None = None
    width: int | None = None
    name: str | None = None
    presets: dict[int, VogelsMotionMountPreset | None] = field(default_factory=dict)
    automove_on: bool | None = None
    automove_id: int | None = None
    ceb_bl_version: str | None = None
    mcp_hw_version: str | None = None
    mcp_bl_version: str | None = None
    mcp_fw_version: str | None = None


class APIConnectionError(HomeAssistantError):
    """Exception class for connection error."""


class APIConnectionDeviceNotFoundError(HomeAssistantError):
    """Exception class for connection error when device was not found."""


# endregion


class API:
    """Bluetooth API."""

    def __init__(
        self,
        hass: HomeAssistant,
        mac: str,
        settings_pin: str | None,
        control_pin: str | None,
        callback: Callable[[VogelsMotionMountData], None],
    ) -> None:
        """Set up the default data."""
        self._hass = hass
        self._mac = mac
        self._settings_pin = settings_pin
        self._control_pin = control_pin
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
        """Test connection to the BLE device once using BleakClient."""
        _LOGGER.debug("Test connection to %s", self._mac)
        if not self._device:
            _LOGGER.error("Device not found with address %s", self._mac)
            raise APIConnectionDeviceNotFoundError("Device not found.")

        try:
            _LOGGER.error(
                "Device found with address %s attempting to connect", self._mac
            )
            await BleakClient(self._device).connect(timeout=120)
        except BleakDeviceNotFoundError as err:
            _LOGGER.error("Failed to connect to device %s", self._mac)
            raise APIConnectionDeviceNotFoundError("Device not found.") from err
        except Exception as err:
            _LOGGER.error("Failed to connect to device %s", self._mac)
            raise APIConnectionError("Error connecting to api.") from err

    async def load_initial_data(self) -> None:
        """Load the initial data from the device."""
        while True:
            try:
                _LOGGER.debug(
                    "Initial data connection to device %s connecting", self._mac
                )
                await self.refreshData()
                break
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Exception while reading initial data %s", err)
            await asyncio.sleep(5)

    async def refreshData(self):
        """Read data from BLE device, connects if necessary."""
        if self._client.is_connected:
            await self._read_current_data()
        else:
            # connect will automatically load data
            await self._connect()

    # region Actions API

    async def select_preset(self, preset_id: int):
        """Select a preset index to move the MotionMount to."""
        await self._connect(
            self._client.write_gatt_char,
            CHAR_PRESET_UUID,
            bytes([preset_id]),
            response=True,
        )

    async def set_distance(self, distance: int):
        """Select a preset index to move the MotionMount to."""
        await self._connect(
            self._client.write_gatt_char,
            CHAR_DISTANCE_UUID,
            int(distance).to_bytes(2, byteorder="big"),
            response=True,
        )

    async def set_rotation(self, rotation: int):
        """Select a preset index to move the MotionMount to."""
        await self._connect(
            self._client.write_gatt_char,
            CHAR_ROTATION_UUID,
            int(rotation).to_bytes(2, byteorder="big"),
            response=True,
        )
        self._update(requested_rotation=rotation)

    # endregion
    # region Change Settings API

    async def set_width(self, width: int):
        """Select a preset index to move the MotionMount to."""
        await self._connect(
            self._client.write_gatt_char, CHAR_WIDTH_UUID, bytes([width]), response=True
        )
        self._update(width=width)

    async def set_name(self, name: str):
        """Select a preset index to move the MotionMount to."""
        newname = bytearray(name.encode("utf-8"))[:20].ljust(20, b"\x00")
        await self._connect(
            self._client.write_gatt_char,
            CHAR_NAME_UUID,
            newname,
            response=True,
        )
        self._update(name=newname)

    async def set_automove(self, id: int | None):
        """Select a automove option where None is off."""
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

    async def set_preset(
        self,
        preset_index: int,
        distance: int | None = None,
        rotation: int | None = None,
        name: str | None = None,
    ):
        """Select a preset index to move the MotionMount to."""
        preset = self._data.presets[preset_index]

        new_preset_id = preset.id
        new_name = name if name is not None else preset.name
        new_distance = distance if distance is not None else preset.distance
        new_rotation = rotation if rotation is not None else preset.rotation

        # TODO max length for name
        name_bytes = (new_name).encode("utf-8")
        id_bytes = bytes([new_preset_id])
        distance_bytes = int(new_distance).to_bytes(2, byteorder="big")
        rotation_bytes = int(new_rotation).to_bytes(2, byteorder="big")

        data = id_bytes + distance_bytes + rotation_bytes + name_bytes
        newpresets = dict(self._data.presets)

        newpresets[preset_index] = VogelsMotionMountPreset(
            id=new_preset_id,
            name=new_name,
            distance=new_distance,
            rotation=new_rotation,
        )
        _LOGGER.debug("set_preset write data to %s", data)
        await self._connect(
            self._client.write_gatt_char,
            CHAR_PRESET_UUIDS[preset_index],
            data[:20].ljust(20, b"\x00"),
            response=True,
        )
        self._update(presets=newpresets)

    # endregion
    # endregion
    # region Private functions

    async def _connect(
        self, connected: Callable[[], Awaitable[None]] = None, *args, **kwargs
    ):
        """Connect and load initial data, skips and loads data if already connected."""

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
            await self._setup_notifications()

        self._update(connected=self._client.is_connected)

        if connected is not None:
            # calls callback before loading data in order to run command with less delay
            await connected(*args, **kwargs)

        if should_read_data:
            # only read data if this was a new connection
            await self._read_current_data()

    def _handle_disconnect(self, _):
        """Update state when client disconnects."""
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
        self._handle_distance_change(
            None, await self._client.read_gatt_char(CHAR_DISTANCE_UUID)
        )
        self._handle_rotation_change(
            None, await self._client.read_gatt_char(CHAR_ROTATION_UUID)
        )
        self._handle_width_change(await self._client.read_gatt_char(CHAR_WIDTH_UUID))
        self._handle_name_change(await self._client.read_gatt_char(CHAR_NAME_UUID))
        for preset_index in range(7):
            self._handle_preset_change(
                preset_index,
                await self._client.read_gatt_char(CHAR_PRESET_UUIDS[preset_index]),
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

    def _handle_distance_change(self, _, data: bytearray):
        _LOGGER.debug("Consume distance change %s", data)
        self._update(distance=int.from_bytes(data, "big"))

    def _handle_rotation_change(self, _, data: bytearray):
        _LOGGER.debug("Consume rotation change %s", data)
        self._update(rotation=int.from_bytes(data, "big"))

    def _handle_width_change(self, data: bytearray):
        _LOGGER.debug("Consume width change %s", data)
        self._update(width=data[0])

    def _handle_name_change(self, data: bytearray):
        _LOGGER.debug("Consume name change %s", data)
        self._update(name=data.decode("utf-8").rstrip("\x00"))

    def _handle_preset_change(self, preset_index, data: bytearray):
        preset_id = preset_index + 1
        # Preset IDs are 1-based because 0 is the default preset
        _LOGGER.debug("Consume preset change for id %s data %s", preset_id, data)
        distance = int.from_bytes(data[1:3], "big")
        rotation = int.from_bytes(data[3:5], "big")
        name = data[5:].decode("utf-8").rstrip("\x00")
        new_presets = dict(self._data.presets)
        new_presets[preset_index] = VogelsMotionMountPreset(
            id=preset_id,
            name=name,
            distance=distance,
            rotation=rotation,
        )
        self._update(presets=new_presets)

    def _handle_automove_change(self, data: bytearray):
        automove_id = int.from_bytes(data, "big")
        _LOGGER.debug("Consume automove change %s", automove_id)
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

    def _handle_version_ceb_change(self, data):
        # data is split across 2 different data sets
        _LOGGER.debug("Consume CEB Version change %s", data)
        self._update(
            ceb_bl_version=".".join(str(b) for b in data),
        )

    def _handle_version_mcp_change(self, data):
        # data is split across 2 different data sets
        _LOGGER.debug("Consume MCP Version change %s", data)
        self._update(
            mcp_hw_version=".".join(str(b) for b in data[:3]),
            mcp_bl_version=".".join(str(b) for b in data[3:5]),
            mcp_fw_version=".".join(str(b) for b in data[5:7]),
        )

    # endregion
