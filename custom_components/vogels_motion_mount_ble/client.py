"""Defines the bluetooth client to control the Vogels Motion Mount."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
import struct

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import (
    CHAR_AUTHENTICATE_UUID,
    CHAR_AUTOMOVE_UUID,
    CHAR_CALIBRATE_UUID,
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
    ChAR_DISABLE_CHANNEL,
)
from .data import (
    VogelsMotionMountAuthenticationStatus,
    VogelsMotionMountAuthenticationType,
    VogelsMotionMountAutoMoveType,
    VogelsMotionMountMultiPinFeatures,
    VogelsMotionMountPermissions,
    VogelsMotionMountPinSettings,
    VogelsMotionMountPreset,
    VogelsMotionMountPresetData,
    VogelsMotionMountVersions,
)

_LOGGER = logging.getLogger(__name__)

# -------------------------------
# region Exceptions
# -------------------------------


class VogelsMotionMountClientAuthenticationError(Exception):
    """Exception class if user is not authorized to do this action."""

    def __init__(self, cooldown: int, message: str = "Unauthorized") -> None:
        """Initialize APIAuthenticationError with cooldown and optional message."""
        super().__init__(message)
        self.cooldown = cooldown

    # -------------------------------
    # endregion
    # region Setup
    # -------------------------------


class VogelsMotionMountBluetoothClient:
    """Bluetooth client for controlling the Vogels Motion Mount.

    Handles connection, authentication, reading and writing characteristics,
    and permission management for the Vogels Motion Mount BLE device.
    """

    def __init__(
        self,
        pin: int | None,
        device: BLEDevice,
        permission_callback: Callable[[VogelsMotionMountPermissions], None],
        connection_callback: Callable[[bool], None],
        distance_callback: Callable[[int], None],
        rotation_callback: Callable[[int], None],
    ) -> None:
        """Initialize the Vogels Motion Mount Bluetooth client.

        Args:
            pin: The PIN code for authentication, or None.
            device: The BLEDevice instance representing the mount.
            permission_callback: Callback for permission updates.
            connection_callback: Callback for connection state changes.
            distance_callback: Callback for distance updates.
            rotation_callback: Callback for rotation updates.
        """
        self._pin = pin
        self._device = device
        self._connection_callback = connection_callback
        self._permission_callback = permission_callback
        self._distance_callback = distance_callback
        self._rotation_callback = rotation_callback
        self._session_data: _VogelsMotionMountSessionData | None = None

    # -------------------------------
    # endregion
    # region Read
    # -------------------------------

    async def read_permissions(self) -> VogelsMotionMountPermissions:
        """Read and return the current permissions for the connected Vogels Motion Mount."""
        return (await self._connect()).permissions

    async def read_automove(self) -> VogelsMotionMountAutoMoveType:
        """Read and return the current automove type for the Vogels Motion Mount."""
        data = await self._read(CHAR_AUTOMOVE_UUID)
        return VogelsMotionMountAutoMoveType(int.from_bytes(data, "big"))

    async def read_distance(self) -> int:
        """Read and return the current distance value from the Vogels Motion Mount."""
        data = await self._read(CHAR_DISTANCE_UUID)
        return int.from_bytes(data, "big")

    async def read_freeze_preset_index(self) -> int:
        """Read and return the index of the current freeze preset from the Vogels Motion Mount."""
        return (await self._read(CHAR_FREEZE_UUID))[0]

    async def read_multi_pin_features(self) -> VogelsMotionMountMultiPinFeatures:
        """Read and return the current multi-pin feature flags from the Vogels Motion Mount."""
        data = (await self._read(CHAR_MULTI_PIN_FEATURES_UUID))[0]
        return VogelsMotionMountMultiPinFeatures(
            change_presets=bool(data & (1 << 0)),
            change_name=bool(data & (1 << 1)),
            disable_channel=bool(data & (1 << 2)),
            change_tv_on_off_detection=bool(data & (1 << 3)),
            change_default_position=bool(data & (1 << 4)),
            start_calibration=bool(data & (1 << 7)),
        )

    async def read_name(self) -> str:
        """Read and return the current name of the Vogels Motion Mount."""
        data = await self._read(CHAR_NAME_UUID)
        return data.decode("utf-8").rstrip("\x00")

    async def read_pin_settings(self) -> VogelsMotionMountPinSettings:
        """Read and return the current pin settings of the Vogels Motion Mount."""
        data = await self._read(CHAR_PIN_SETTINGS_UUID)
        return VogelsMotionMountPinSettings(int(data[0]))

    async def read_presets(self) -> list[VogelsMotionMountPreset]:
        """Read and return a list of all preset configurations from the Vogels Motion Mount."""
        return [
            await self.read_preset(index) for index in range(len(CHAR_PRESET_UUIDS))
        ]

    async def read_preset(self, index: int) -> VogelsMotionMountPreset:
        """Read and return the preset configuration at the specified index."""
        data = await self._read(CHAR_PRESET_UUIDS[index]) + await self._read(
            CHAR_PRESET_NAMES_UUIDS[index]
        )
        if data[0] != 0:
            data = VogelsMotionMountPresetData(
                distance=max(0, min(int.from_bytes(data[1:3], "big"), 100)),
                name=data[5:].decode("utf-8").rstrip("\x00"),
                rotation=max(
                    -100, min(int.from_bytes(data[3:5], "big", signed=True), 100)
                ),
            )
        else:
            data = None

        return VogelsMotionMountPreset(
            index=index,
            data=data,
        )

    async def read_rotation(self) -> int:
        """Read and return the current rotation value from the Vogels Motion Mount."""
        data = await self._read(CHAR_ROTATION_UUID)
        return int.from_bytes(data, "big")

    async def read_tv_width(self) -> int:
        """Read and return the width of the TV from the Vogels Motion Mount."""
        return (await self._read(CHAR_NAME_UUID))[0]

    async def read_versions(self) -> VogelsMotionMountVersions:
        """Read and return the firmware and hardware version information from the Vogels Motion Mount."""
        data_ceb = await self._read(CHAR_VERSIONS_CEB_UUID)
        data_mcp = await self._read(CHAR_VERSIONS_MCP_UUID)
        return VogelsMotionMountVersions(
            ceb_bl_version=".".join(str(b) for b in data_ceb),
            mcp_hw_version=".".join(str(b) for b in data_mcp[:3]),
            mcp_bl_version=".".join(str(b) for b in data_mcp[3:5]),
            mcp_fw_version=".".join(str(b) for b in data_mcp[5:7]),
        )

    # -------------------------------
    # endregion
    # region Control
    # -------------------------------

    async def disconnect(self):
        """Disconnect from the Vogels Motion Mount BLE device if connected."""
        if self._session_data:
            await self._session_data.client.disconnect()

    async def select_preset(self, preset_index: int):
        """Select the preset at the given index on the Vogels Motion Mount."""
        assert preset_index in range(8)
        await self._write(CHAR_PRESET_UUID, bytes([preset_index]))

    async def start_calibration(self):
        """Start the calibration process on the Vogels Motion Mount."""
        await self._write(CHAR_CALIBRATE_UUID, bytes([1]))

    # -------------------------------
    # endregion
    # region Write
    # -------------------------------

    async def set_authorised_user_pin(self, pin: str):
        """Set the authorised user PIN on the Vogels Motion Mount."""
        assert pin.isdigit()
        assert len(pin) == 4
        await self._write(
            char_uuid=CHAR_CHANGE_PIN_UUID,
            data=int(pin).to_bytes(2, byteorder="little"),
        )

    async def set_automove(self, automove: VogelsMotionMountAutoMoveType):
        """Set the automove type on the Vogels Motion Mount."""
        await self._write(
            char_uuid=CHAR_AUTOMOVE_UUID,
            data=int(automove.value).to_bytes(2, byteorder="big"),
        )

    async def set_distance(self, distance: int):
        """Set the distance value on the Vogels Motion Mount."""
        assert distance in range(101)
        await self._write(
            char_uuid=CHAR_DISTANCE_UUID,
            data=int(distance).to_bytes(2, byteorder="big"),
        )

    async def set_freeze_preset(self, preset_index: int):
        """Set the freeze preset index on the Vogels Motion Mount."""
        assert preset_index in range(8)
        await self._write(
            char_uuid=CHAR_FREEZE_UUID,
            data=bytes([preset_index]),
        )

    async def set_multi_pin_features(self, features: VogelsMotionMountMultiPinFeatures):
        """Set the multi-pin features on the Vogels Motion Mount."""
        value = 0
        value |= int(features.change_presets) << 0
        value |= int(features.change_name) << 1
        value |= int(features.disable_channel) << 2
        value |= int(features.change_tv_on_off_detection) << 3
        value |= int(features.change_default_position) << 4
        value |= int(features.start_calibration) << 7
        await self._write(
            char_uuid=CHAR_MULTI_PIN_FEATURES_UUID,
            data=bytes([value]),
        )

    async def set_name(self, name: str):
        """Set the name of the Vogels Motion Mount."""
        assert len(name) in range(1, 21)
        await self._write(
            char_uuid=CHAR_NAME_UUID,
            data=bytearray(name.encode("utf-8"))[:20].ljust(20, b"\x00"),
        )

    async def set_preset(self, preset: VogelsMotionMountPreset):
        """Set the data of a preset on the Vogels Motion Mount."""
        assert preset.index in range(7)
        if preset.data:
            assert preset.data.distance in range(101)
            assert preset.data.rotation in range(-100, 101)
            assert len(preset.data.name) in range(1, 33)
            data = (
                bytes(0x01)
                + int(preset.data.distance).to_bytes(2, byteorder="big")
                + int(preset.data.rotation).to_bytes(2, byteorder="big")
                + preset.data.name.encode("utf-8")
            )
        else:
            data = bytes(0x01)

        await self._write(
            char_uuid=CHAR_PRESET_UUIDS[preset.index],
            data=data[:20].ljust(20, b"\x00"),
        )
        await self._write(
            char_uuid=CHAR_PRESET_NAMES_UUIDS[preset.index],
            data=data[20:].ljust(17, b"\x00"),
        )

    async def set_rotation(self, rotation: int):
        """Set the rotation value on the Vogels Motion Mount."""
        assert rotation in range(-100, 101)
        await self._write(
            char_uuid=CHAR_ROTATION_UUID,
            data=int(rotation).to_bytes(2, byteorder="big"),
        )

    async def set_supervisior_pin(self, pin: str):
        """Set the supervisior PIN on the Vogels Motion Mount."""
        assert len(pin) == 4
        assert pin.isdigit()
        await self._write(
            char_uuid=CHAR_CHANGE_PIN_UUID, data=_encode_supervisior_pin(int(pin))
        )

    async def set_tv_width(self, width: int):
        """Set the width of the TV in cm on the Vogels Motion Mount."""
        assert width in range(1, 244)
        await self._write(
            char_uuid=CHAR_WIDTH_UUID,
            data=bytes([width]),
        )

    # -------------------------------
    # endregion
    # region Connection
    # -------------------------------

    async def _connect(self) -> _VogelsMotionMountSessionData:
        """Connect to the device if not already connected. Read auth status and store it in session data."""
        if self._session_data:
            return self._session_data

        client = await establish_connection(
            client_class=BleakClientWithServiceCache,
            device=self._device,
            name=self._device.name or "Unknown Device",
            disconnected_callback=self._handle_disconnect,
        )

        self._session_data = _VogelsMotionMountSessionData(
            client=client,
            permissions=await get_permissions(client, self._pin),
        )
        self._permission_callback(self._session_data.permissions)
        self._connection_callback(self._session_data.client.is_connected)
        return self._session_data

    def _handle_disconnect(self, _: BleakClient):
        """Reset session and call connection callback."""
        self._session_data = None
        self._connection_callback(False)

    async def _read(self, char_uuid: str) -> bytes:
        """Read data by first connecting and then returning the read data."""
        session_data = await self._connect()
        return await session_data.client.read_gatt_char(char_uuid)

    async def _write(self, char_uuid: str, data: bytes):
        """Writes data by first connecting, checking permission status and then writing data. Also reads updated data that is then returned to be verified."""
        session_data = await self._connect()
        if not self._has_write_permission(char_uuid, session_data.permissions):
            raise VogelsMotionMountClientAuthenticationError(cooldown=0)
        await session_data.client.write_gatt_char(char_uuid, data)

    def _has_write_permission(
        self, char_uuid: str, permissions: VogelsMotionMountPermissions
    ) -> bool:
        return (
            (char_uuid == CHAR_PRESET_UUIDS and permissions.change_presets)
            or (char_uuid == CHAR_PRESET_NAMES_UUIDS and permissions.change_presets)
            or (char_uuid == CHAR_NAME_UUID and permissions.change_name)
            or (char_uuid == ChAR_DISABLE_CHANNEL and permissions.disable_channel)
            or (
                char_uuid == CHAR_FREEZE_UUID and permissions.change_tv_on_off_detection
            )
            or (char_uuid == CHAR_CALIBRATE_UUID and permissions.start_calibration)
            or permissions.change_settings
        )

    # -------------------------------
    # endregion
    # region Permission
    # -------------------------------


async def get_permissions(
    client: BleakClient, pin: int | None
) -> VogelsMotionMountPermissions:
    """Check permissions by evaluating auth_type and reading multi pin features only if necessary."""
    max_auth_status = await _get_max_auth_status(client, pin)
    if max_auth_status == VogelsMotionMountAuthenticationType.Full:
        return VogelsMotionMountPermissions(
            max_auth_status, True, True, True, True, True, True, True
        )
    if max_auth_status == VogelsMotionMountAuthenticationType.Control:
        multi_pin_features = await _read_multi_pin_features_directly(client)
        return VogelsMotionMountPermissions(
            auth_status=max_auth_status,
            change_settings=False,
            change_default_position=multi_pin_features.change_default_position,
            change_name=multi_pin_features.change_name,
            change_presets=multi_pin_features.change_presets,
            change_tv_on_off_detection=multi_pin_features.change_tv_on_off_detection,
            disable_channel=multi_pin_features.disable_channel,
            start_calibration=multi_pin_features.start_calibration,
        )
    return VogelsMotionMountPermissions(
        max_auth_status, False, False, False, False, False, False, False
    )


async def _get_max_auth_status(
    client: BleakClient, pin: int | None
) -> VogelsMotionMountAuthenticationStatus:
    """Check auth status by sending pin and checking auth data afterwards."""
    # if there is no pin it's not possible to authenticate, use the current data
    if not pin:
        return await _get_auth_status(client)

    # first try to authenticate as supervisior, if it doesn't work then authorised user
    supervisior_pin_data = _encode_supervisior_pin(pin)
    await client.write_gatt_char(CHAR_AUTHENTICATE_UUID, supervisior_pin_data)
    current_auth_type = await _get_auth_status(client)

    if current_auth_type is not VogelsMotionMountAuthenticationType.Wrong:
        return current_auth_type

    authorised_user_pin_data = pin.to_bytes(2, "little")
    await client.write_gatt_char(CHAR_AUTHENTICATE_UUID, authorised_user_pin_data)
    return await _get_auth_status(client)


async def _get_auth_status(
    client: BleakClient,
) -> VogelsMotionMountAuthenticationStatus:
    """Read the auth type for the current user."""
    # read pin permission
    _auth_info = await client.read_gatt_char(CHAR_PIN_CHECK_UUID)
    if _auth_info.startswith(b"\x80\x80"):
        return VogelsMotionMountAuthenticationStatus(
            auth_type=VogelsMotionMountAuthenticationType.Full,
            cooldown=None,
        )
    if _auth_info.startswith(b"\x80"):
        return VogelsMotionMountAuthenticationStatus(
            auth_type=VogelsMotionMountAuthenticationType.Control,
            cooldown=None,
        )
    # check if there was a wrong pin and therefore cooldown is active
    return VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Wrong,
        cooldown=max(0, 3 * (struct.unpack("<I", _auth_info)[0]) - 10),
    )


async def _read_multi_pin_features_directly(
    client: BleakClient,
) -> VogelsMotionMountMultiPinFeatures:
    """Read multi pin features directly without connecting first."""
    data = (await client.read_gatt_char(CHAR_MULTI_PIN_FEATURES_UUID))[0]
    return VogelsMotionMountMultiPinFeatures(
        change_presets=bool(data & (1 << 0)),
        change_name=bool(data & (1 << 1)),
        disable_channel=bool(data & (1 << 2)),
        change_tv_on_off_detection=bool(data & (1 << 3)),
        change_default_position=bool(data & (1 << 4)),
        start_calibration=bool(data & (1 << 7)),
    )


def _encode_supervisior_pin(pin: int) -> bytes:
    return bytes([pin & 0xFF, (((pin >> 8) & 0xFF) + 0x40) & 0xFF])


@dataclass
class _VogelsMotionMountSessionData:
    client: BleakClient
    permissions: VogelsMotionMountPermissions

    # -------------------------------
    # endregion
    # -------------------------------
