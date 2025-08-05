"""Bluetooth api to connect to Vogels MotionMount and send and recieve data."""

import asyncio
from dataclasses import dataclass, field, replace
import logging

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError

from homeassistant.core import Callable
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
    CHAR_WIDTH_UUID,
)

_LOGGER = logging.getLogger(__name__)


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


class API:
    """Bluetooth API."""

    def __init__(
        self,
        mac: str,
        settings_pin: str | None,
        control_pin: str | None,
        callback: Callable[[VogelsMotionMountData], None],
    ) -> None:
        """Set up the default data."""
        self._mac = mac
        self._settings_pin = settings_pin
        self._control_pin = control_pin
        self._callback = callback
        self._data = VogelsMotionMountData(connected=False)
        self._client: BleakClient = BleakClient(
            self._mac, disconnected_callback=self._handle_disconnect, timeout=120
        )
        self._disconnected_event = asyncio.Event()
        self._connected_event = asyncio.Event()
        self._maintain_connection = False
        self._initial_data_loaded = False

    async def test_connection(self):
        """Test connection to the BLE device once using BleakClient."""
        _LOGGER.debug("start test connection")
        device = await BleakScanner.find_device_by_address(self._mac, timeout=120)
        if not device:
            _LOGGER.error("Device not found with name %s", self._mac)
            raise APIConnectionDeviceNotFoundError("Device not found.")

        try:
            await BleakClient(device).connect(timeout=120)
        except BleakDeviceNotFoundError as err:
            _LOGGER.error("Failed to connect to device, not found: %s", err)
            raise APIConnectionDeviceNotFoundError("Device not found.") from err
        except Exception as err:
            _LOGGER.error("Failed to connect to device: %s", err)
            raise APIConnectionError("Error connecting to api.") from err

    async def wait_for_ble_backend(self, timeout):
        """Wait until BLE backend is available or timeout."""
        total_wait = 0
        while total_wait < timeout:
            try:
                await BleakScanner.discover(timeout=1)
                _LOGGER.debug("Bakend Ready!")
            except BleakError as e:
                _LOGGER.debug("BLE backend not ready yet %s!", e)
                await asyncio.sleep(5)
                total_wait += 5

        raise RuntimeError("BLE backend not available after waiting.")

    def _update(self, **kwargs):
        # Update one or more fields, retaining others from existing data. Then notify the coordinator.
        self._data = replace(self._data, **kwargs)
        self._callback(self._data)

    def _handle_disconnect(self, _):
        _LOGGER.debug("handle Device disconnected!")
        self._connected_event.clear()
        self._disconnected_event.set()
        self._update(connected=self._client.is_connected)

    async def _connect(self):
        _LOGGER.debug("connecting... to %s", self._mac)
        await self._client.connect(timeout=120)
        self._disconnected_event.clear()
        _LOGGER.debug("connected! to %s", self._mac)
        self._update(connected=self._client.is_connected)
        await self._setup_notifications()
        await self._read_initial_data()
        self._connected_event.set()

    def _handle_distance_change(self, _, data: bytearray):
        _LOGGER.debug("distance change %s", data)
        self._update(distance=int.from_bytes(data, "big"))

    def _handle_rotation_change(self, _, data: bytearray):
        _LOGGER.debug("rotation change %s", data)
        self._update(rotation=int.from_bytes(data, "big"))

    def _handle_width_change(self, data: bytearray):
        _LOGGER.debug("width change %s", data)
        self._update(width=data[0])

    def _handle_name_change(self, data: bytearray):
        _LOGGER.debug("name change %s", data)
        self._update(name=data.decode("utf-8").rstrip("\x00"))

    def _handle_preset_change(self, preset_index, data: bytearray):
        preset_id = preset_index + 1
        # Preset IDs are 1-based because 0 is the default preset
        _LOGGER.debug("_handle_preset_change for id %s data %s", preset_id, data)
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
        _LOGGER.debug("automove change %s", automove_id)
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

    async def _setup_notifications(self):
        _LOGGER.debug("_setup_notifications")
        await self._client.start_notify(
            char_specifier=CHAR_DISTANCE_UUID,
            callback=self._handle_distance_change,
        )
        await self._client.start_notify(
            char_specifier=CHAR_ROTATION_UUID,
            callback=self._handle_rotation_change,
        )

    async def _read_initial_data(self):
        _LOGGER.debug("_read_initial_data")
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

    async def load_initial_data(self):
        """Load the initial data from the device."""
        # TODO make it optional if the connection should be maintained or connect on command (when required to send command) or poll time
        while not self._initial_data_loaded:
            try:
                _LOGGER.debug(
                    "initial data connection to device %s connecting ...", self._mac
                )
                await self._connect()

                self._initial_data_loaded = True
            except Exception:
                # TODO catch bleak.exc.BleakError: No backend with an available connection slot that can reach address D9:13:5D:AB:3B:37 was found
                _LOGGER.exception("Exception while connecting/connected")
                await asyncio.sleep(5)

    async def maintain_connection(self):
        """Maintain connection to device."""
        self._maintain_connection = True
        # TODO make it optional if the connection should be maintained or connect on command (when required to send command) or poll time
        while True:
            try:
                _LOGGER.debug(
                    "Maintain connection to device %s connecting ...", self._mac
                )
                await self._connect()

                await self._disconnected_event.wait()

                _LOGGER.debug(
                    "maintain device disconnected %s", self._client.is_connected
                )

                # reset events
                self._update(connected=self._client.is_connected)
                await asyncio.sleep(1)
            except Exception:
                # TODO catch bleak.exc.BleakError: No backend with an available connection slot that can reach address D9:13:5D:AB:3B:37 was found
                _LOGGER.exception("Exception while connecting/connected")
                await asyncio.sleep(5)

    async def _wait_for_connection(self):
        if self._maintain_connection:
            _LOGGER.debug("Wait for maintained connection")
            await self._connected_event.wait()
        elif self._client.is_connected:
            _LOGGER.debug("Already connected, no need to connect again.")
            return
        else:
            _LOGGER.debug("Wait for new connection, connecting...")
            await self._connect()

    async def select_preset(self, preset_id: int):
        """Select a preset index to move the MotionMount to."""
        await self._wait_for_connection()
        await self._client.write_gatt_char(
            CHAR_PRESET_UUID, bytes([preset_id]), response=True
        )

    async def set_width(self, width: int):
        """Select a preset index to move the MotionMount to."""
        await self._wait_for_connection()
        await self._client.write_gatt_char(
            CHAR_WIDTH_UUID, bytes([width]), response=True
        )

    async def set_distance(self, distance: int):
        """Select a preset index to move the MotionMount to."""
        await self._wait_for_connection()
        await self._client.write_gatt_char(
            CHAR_DISTANCE_UUID,
            int(distance).to_bytes(2, byteorder="big"),
            response=True,
        )
        # TODO how to know that it is finished?

    async def set_rotation(self, rotation: int):
        """Select a preset index to move the MotionMount to."""
        self._update(requested_rotation=rotation)
        await self._wait_for_connection()
        await self._client.write_gatt_char(
            CHAR_ROTATION_UUID,
            int(rotation).to_bytes(2, byteorder="big"),
            response=True,
        )
        # TODO how to know that it is finished?

    async def set_name(self, name: str):
        """Select a preset index to move the MotionMount to."""
        await self._wait_for_connection()
        newname = bytearray(name.encode("utf-8"))[:20].ljust(20, b"\x00")
        await self._client.write_gatt_char(CHAR_NAME_UUID, newname, response=True)
        self._update(name=name)

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

        await self._wait_for_connection()
        await self._client.write_gatt_char(
            CHAR_AUTOMOVE_UUID, int(data).to_bytes(2, byteorder="big")
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
        await self._wait_for_connection()
        preset = self._data.presets[preset_index]
        distance_bytes = (
            distance if distance is not None else preset.distance
        ).to_bytes(2, byteorder="big")
        rotation_bytes = (
            rotation if rotation is not None else preset.rotation
        ).to_bytes(2, byteorder="big")
        name_bytes = (name if name is not None else preset.name).encode("utf-8")
        data = bytes([preset.id]) + distance_bytes + rotation_bytes + name_bytes
        newpresets = dict(self._data.presets)
        newpresets[preset_index] = replace(
            preset, name=name, distance=distance, rotation=rotation
        )
        await self._client.write_gatt_char(
            CHAR_PRESET_UUIDS[preset_index], data, response=True
        )
        self._update(presets=newpresets)


class APIConnectionError(HomeAssistantError):
    """Exception class for connection error."""


class APIConnectionDeviceNotFoundError(HomeAssistantError):
    """Exception class for connection error when device was not found."""
