from bleak import BleakClient, BleakScanner
import logging
import asyncio
from .const import CHAR_DISTANCE_UUID, CHAR_ROTATION_UUID, CHAR_PRESET_UUIDS
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    # Create an instance of your sensor entity
    handler = BluetoothDeviceHandler(entry.data["mac_address"], hass)
    # Add entity to Home Assistant
    async_add_entities(handler)


class BluetoothDeviceHandler:
    def __init__(self, address, hass):
        self._attr_name = "Bluetooth Connection Status"
        self._attr_unique_id = f"bluetooth_{address.replace(':', '').lower()}"
        self._address = address
        self._connected = False
        self._hass = hass
        self._client = None
        self._task = None
        self._disconnect_event = None

    def register(self):
        logger.debug("register")
        self._task = self._hass.loop.create_task(self.monitor())

    async def monitor(self):
        while True:
            logger.debug("scanning for device")
            device = await BleakScanner.find_device_by_address(self._address)

            if device is None:
                logger.debug("no device found, wait then scan again")
                await asyncio.sleep(5)
                continue

            disconnect_event = asyncio.Event()

            try:
                logger.debug("connecting to device")
                async with BleakClient(
                    device, disconnected_callback=disconnect_event.set()
                ) as client:
                    logger.debug("connected to device")
                    self._client = client
                    self._connected = True
                    await disconnect_event.wait()
                    logger.debug("device disconnected")
                    self._connected = False
            except Exception:
                logger.exception("exception while connecting/connected")
                await asyncio.sleep(5)

    @property
    def device_info(self):
        return {
            "identifiers": {("vogels_motion_mount", self._mac_address)},
            "manufacturer": "Custom Bluetooth Inc.",
            "model": "BT Device",
            "connections": {("mac", self._mac_address)},
        }

    @property
    def native_value(self):
        return self._connected

    @property
    def extra_state_attributes(self):
        return {
            "mac_address": self._address,
            "connected": self._connected,
        }

    async def is_connected(self):
        return self.client.is_connected

    async def get_distance(self):
        data = await self.client.read_gatt_char(CHAR_DISTANCE_UUID)
        return int.from_bytes(data[0:2], "little")

    async def set_distance(self, value: int):
        await self.client.write_gatt_char(
            CHAR_DISTANCE_UUID, value.to_bytes(2, "little")
        )

    async def get_rotation(self):
        data = await self.client.read_gatt_char(CHAR_ROTATION_UUID)
        return int.from_bytes(data[0:2], "little", signed=True)

    async def set_rotation(self, value: int):
        await self.client.write_gatt_char(
            CHAR_ROTATION_UUID, value.to_bytes(2, "little", signed=True)
        )

    async def get_presets(self):
        presets = []
        for uuid in CHAR_PRESET_UUIDS:
            raw = await self.client.read_gatt_char(uuid)
            if len(raw) < 4:
                continue
            distance = int.from_bytes(raw[0:2], "little")
            rotation = int.from_bytes(raw[2:4], "little", signed=True)
            name = raw[4:].decode("utf-8", errors="ignore").strip("\x00").strip()
            presets.append(
                {"uuid": uuid, "distance": distance, "rotation": rotation, "name": name}
            )
        return presets

    async def async_will_remove_from_hass(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
