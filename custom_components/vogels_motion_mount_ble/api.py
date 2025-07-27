"""API Placeholder.

You should create your api seperately and have it hosted on PYPI.  This is included here for the sole purpose
of making this example code executable.
"""

import asyncio
from dataclasses import dataclass, replace
import logging
from .const import CHAR_DISTANCE_UUID, CHAR_ROTATION_UUID, CHAR_PRESET_UUID
from bleak import BleakClient, BleakScanner

_LOGGER = logging.getLogger(__name__)

@dataclass
class VogelsMotionMountData:
    """Class to hold api data."""

    connected: bool = False
    distance: int | None = None
    rotation: int | None = None

class API:
    """Class for example API."""

    def __init__(self, mac: str, pin: str | None, coordinator) -> None:
        """Initialise."""
        self._mac = mac
        self._pin = pin
        self._coordinator = coordinator
        self._data = VogelsMotionMountData(connected=False)
        self._client: BleakClient | None = None
        self._disconnected_event = asyncio.Event()

    async def testConnect(self):
        """Test connection to the BLE device once using BleakClient."""
        try:
            _LOGGER.debug("start test connection")
            async with BleakClient(self._mac, timeout=120) as client:
                _LOGGER.debug("Connected to device: %s", client.is_connected)
        except Exception as err:
            _LOGGER.error("Failed to connect to device: %s", err)
            raise APIConnectionError("Error connecting to api.") from err


    async def perform_action(self):
        _LOGGER.exception("write_gatt_char")
        result = await self._client.write_gatt_char(CHAR_PRESET_UUID, bytes([1]), response=True)
        _LOGGER.exception("write_gatt_char result: %s", result)

    def update(self, **kwargs):
        """Update one or more fields, retaining others from existing data. Then notify the coordinator."""
        self._data = replace(self._data, **kwargs)
        self._coordinator.async_set_updated_data(self._data)

    def _handle_disconnect(self, _):
        _LOGGER.debug("handle Device disconnected!")
        self._disconnected_event.set()

    def _handle_distance_change(self, _, data):
        _LOGGER.debug("distance change %s", data)
        self.update(distance=int.from_bytes(data, "little"))

    def _handle_rotation_change(self, _, data):
        _LOGGER.debug("rotation change %s", data)
        self.update(rotation=int.from_bytes(data, "little"))

    # todo make it optional if the connection should be maintained or connect on command (when required to send command) or poll time
    async def maintainConnection(self):
        """Maintain connection to device."""
        while True:
            _LOGGER.debug("scanning for device %s", self._mac)
            device = await BleakScanner.find_device_by_address(self._mac)

            if device is None:
                _LOGGER.debug("no device %s found, wait then scan again", self._mac)
                await asyncio.sleep(5)
                continue

            try:
                _LOGGER.debug("connecting to device")
                async with BleakClient(device, disconnected_callback=self._handle_disconnect, timeout=120) as client:
                    self.connected = client.is_connected
                    self._client = client
                    _LOGGER.debug("maintain connected to device %s", self._client.is_connected)
                    self.update(connected = self._client.is_connected)

                    self._handle_distance_change(None, await client.read_gatt_char(CHAR_DISTANCE_UUID))
                    self._handle_rotation_change(None, await client.read_gatt_char(CHAR_ROTATION_UUID))

                    await client.start_notify(CHAR_DISTANCE_UUID, self._handle_distance_change)
                    await client.start_notify(CHAR_ROTATION_UUID, self._handle_rotation_change)

                    await self._disconnected_event.wait()
                    # reset event
                    self._disconnected_event.clear()
                    _LOGGER.debug("device disconnected %s", self.connected)
                    self.update(connected = client.is_connected)
                    await asyncio.sleep(1)
            except Exception:
                # catch bleak.exc.BleakError: No backend with an available connection slot that can reach address D9:13:5D:AB:3B:37 was found
                _LOGGER.exception("Exception while connecting/connected")
                await asyncio.sleep(5)


class APIConnectionError(Exception):
    """Exception class for connection error."""
