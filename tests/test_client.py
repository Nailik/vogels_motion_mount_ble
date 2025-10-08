"""Tests for bluetooth client interface."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from bleak import BleakClient
from bleak.backends.device import BLEDevice
import pytest

from custom_components.vogels_motion_mount_ble.client import (
    VogelsMotionMountBluetoothClient,
    VogelsMotionMountClientAuthenticationError,
    _encode_supervisior_pin,
    _get_auth_status,
    _get_max_auth_status,
    _read_multi_pin_features_directly,
    _VogelsMotionMountSessionData,
    get_permissions,
)
from custom_components.vogels_motion_mount_ble.const import (
    CHAR_AUTHENTICATE_UUID,
    CHAR_AUTOMOVE_UUID,
    CHAR_CALIBRATE_UUID,
    CHAR_CHANGE_PIN_UUID,
    CHAR_DISTANCE_UUID,
    CHAR_FREEZE_UUID,
    CHAR_NAME_UUID,
    CHAR_PIN_SETTINGS_UUID,
    CHAR_PRESET_NAMES_UUIDS,
    CHAR_PRESET_UUIDS,
    CHAR_ROTATION_UUID,
    CHAR_VERSIONS_CEB_UUID,
    CHAR_VERSIONS_MCP_UUID,
    CHAR_WIDTH_UUID,
)
from custom_components.vogels_motion_mount_ble.data import (
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

from .conftest import MOCKED_CONF_MAC, MOCKED_CONF_NAME, MOCKED_CONF_PIN  # noqa: TID251


@pytest.fixture
def mock_dev() -> BLEDevice:
    """Mock a BLEDevice."""
    return BLEDevice(address=MOCKED_CONF_MAC, name=MOCKED_CONF_NAME, details={})


@pytest.fixture
def callbacks():
    """Provide mocked callbacks."""
    return {
        "permission": Mock(),
        "connection": Mock(),
        "distance": Mock(),
        "rotation": Mock(),
    }


@pytest.fixture
def client(mock_dev: BLEDevice, callbacks: dict) -> VogelsMotionMountBluetoothClient:
    """Return a Bluetooth client with mocked callbacks."""
    return VogelsMotionMountBluetoothClient(
        pin=MOCKED_CONF_PIN,
        device=mock_dev,
        permission_callback=callbacks["permission"],
        connection_callback=callbacks["connection"],
        distance_callback=callbacks["distance"],
        rotation_callback=callbacks["rotation"],
    )


@pytest.fixture
def mock_ble_client() -> BleakClient:
    """Return a mock Bleak client for session.client."""
    client = AsyncMock()
    client.read_gatt_char = AsyncMock()
    client.write_gatt_char = AsyncMock()
    client.start_notify = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_connected = True
    return client


@pytest.fixture
def mock_session(mock_ble_client: BleakClient) -> _VogelsMotionMountSessionData:
    """Create a mock session data."""
    perms = VogelsMotionMountPermissions(
        auth_status=None,
        change_settings=True,
        change_default_position=True,
        change_name=True,
        change_presets=True,
        change_tv_on_off_detection=True,
        disable_channel=True,
        start_calibration=True,
    )
    return _VogelsMotionMountSessionData(client=mock_ble_client, permissions=perms)


# -------------------------------
# region Read tests
# -------------------------------


@pytest.mark.asyncio
async def test_read_permissions(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Reading permissions returns correct data and does not trigger callback again."""
    perms = VogelsMotionMountPermissions(
        auth_status=None,
        change_presets=True,
        change_name=True,
        change_settings=True,
        change_tv_on_off_detection=True,
        disable_channel=True,
        change_default_position=True,
        start_calibration=True,
    )
    client._connect = AsyncMock(  # noqa: SLF001
        return_value=_VogelsMotionMountSessionData(
            client=mock_session, permissions=perms
        )
    )
    result = await client.read_permissions()
    assert result.change_name is True


@pytest.mark.asyncio
async def test_read_automove(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should decode the automove value into VogelsMotionMountAutoMoveType."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = (1).to_bytes(1, "big")

    result = await client.read_automove()

    assert result == VogelsMotionMountAutoMoveType.Hdmi_1_Off
    mock_session.client.read_gatt_char.assert_awaited_once_with(CHAR_AUTOMOVE_UUID)


@pytest.mark.asyncio
async def test_read_distance(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Reading distance returns correct integer value."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = (42).to_bytes(2, "big")
    distance = await client.read_distance()
    assert distance == 42


@pytest.mark.asyncio
async def test_read_freeze_preset_index(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should return the freeze preset index from the correct characteristic."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = bytes([3])
    result = await client.read_freeze_preset_index()
    assert result == 3
    mock_session.client.read_gatt_char.assert_awaited_once_with(CHAR_FREEZE_UUID)


@pytest.mark.asyncio
async def test_read_multi_pin_features(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Read multi-pin features parses bits correctly."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = bytes([0b10011111])
    features = await client.read_multi_pin_features()
    assert features.start_calibration is True
    assert features.change_name is True


@pytest.mark.asyncio
async def test_read_name(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Reading name returns correct string value."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = b"MyMount\x00"
    name = await client.read_name()
    assert name == "MyMount"


@pytest.mark.asyncio
async def test_read_pin_settings(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should decode and return VogelsMotionMountPinSettings."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = bytes([12])
    result = await client.read_pin_settings()
    assert isinstance(result, VogelsMotionMountPinSettings)
    assert result.value == 12
    mock_session.client.read_gatt_char.assert_awaited_once_with(CHAR_PIN_SETTINGS_UUID)


@pytest.mark.asyncio
async def test_read_presets(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should read all presets and decode them into VogelsMotionMountPreset list."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    preset_data = (
        b"\x01"
        + (50).to_bytes(2, "big")
        + (10).to_bytes(2, "big", signed=True)
        + b"LivingRoom"
    )
    mock_session.client.read_gatt_char.side_effect = [
        preset_data[:20],
        preset_data[20:].ljust(17, b"\x00"),
    ] * len(CHAR_PRESET_UUIDS)

    result = await client.read_presets()

    assert all(isinstance(p, VogelsMotionMountPreset) for p in result)
    assert isinstance(result[0].data, VogelsMotionMountPresetData)
    assert result[0].data.distance == 50
    assert result[0].data.rotation == 10
    assert "LivingRoom" in result[0].data.name


@pytest.mark.asyncio
async def test_read_presets_with_empty_data(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should return preset with data=None when the first byte is 0."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    empty_data = b"\x00" + b"\x00" * 19
    mock_session.client.read_gatt_char.side_effect = [
        empty_data,
        b"\x00" * 17,
    ] * len(CHAR_PRESET_UUIDS)
    result = await client.read_presets()
    assert all(isinstance(p, VogelsMotionMountPreset) for p in result)
    assert result[0].data is None


@pytest.mark.asyncio
async def test_read_rotation(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Reading rotation returns correct integer value."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = (25).to_bytes(2, "big")
    rotation = await client.read_rotation()
    assert rotation == 25


@pytest.mark.asyncio
async def test_read_tv_width(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should return the first byte as TV width."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.return_value = bytes([120])

    result = await client.read_tv_width()

    assert result == 120
    mock_session.client.read_gatt_char.assert_awaited_once_with(CHAR_WIDTH_UUID)


@pytest.mark.asyncio
async def test_read_versions(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """It should return VogelsMotionMountVersions decoded from CEB and MCP UUIDs."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.client.read_gatt_char.side_effect = [
        bytes([1, 2, 3]),  # CEB version
        bytes([4, 5, 6, 7, 8, 9, 10]),  # MCP version
    ]

    result = await client.read_versions()

    assert isinstance(result, VogelsMotionMountVersions)
    assert result.ceb_bl_version == "1.2.3"
    assert result.mcp_hw_version == "4.5.6"
    assert result.mcp_bl_version == "7.8"
    assert result.mcp_fw_version == "9.10"
    mock_session.client.read_gatt_char.assert_any_await(CHAR_VERSIONS_CEB_UUID)
    mock_session.client.read_gatt_char.assert_any_await(CHAR_VERSIONS_MCP_UUID)


# -------------------------------
# region Control tests
# -------------------------------


@pytest.mark.asyncio
async def test_select_preset_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Selecting a preset writes correct bytes."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.select_preset(3)
    mock_session.client.write_gatt_char.assert_called_once()


@pytest.mark.asyncio
async def test_start_calibration_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Starting calibration writes correct byte."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.start_calibration()
    mock_session.client.write_gatt_char.assert_called_once_with(
        CHAR_CALIBRATE_UUID, bytes([1])
    )


@pytest.mark.asyncio
async def test_disconnect(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Disconnect clears session and disconnects client."""
    client._session_data = mock_session  # noqa: SLF001
    await client.disconnect()
    mock_session.client.disconnect.assert_awaited_once()


# -------------------------------
# region Write tests
# -------------------------------


@pytest.mark.asyncio
async def test_request_distance_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Requesting distance writes correct bytes."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.request_distance(55)
    mock_session.client.write_gatt_char.assert_called_once_with(
        CHAR_DISTANCE_UUID, (55).to_bytes(2, "big")
    )


@pytest.mark.asyncio
async def test_request_rotation_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Requesting rotation writes correct bytes."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.request_rotation(-25)
    mock_session.client.write_gatt_char.assert_called_once_with(
        CHAR_ROTATION_UUID, (-25).to_bytes(2, "big", signed=True)
    )


@pytest.mark.asyncio
async def test_set_authorised_user_pin_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """set_authorised_user_pin writes the little-endian 2-byte PIN when permissions allow."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.set_authorised_user_pin("1234")
    expected = int("1234").to_bytes(2, byteorder="little")
    mock_session.client.write_gatt_char.assert_awaited_once_with(
        CHAR_CHANGE_PIN_UUID, expected
    )


@pytest.mark.asyncio
async def test_set_automove_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Set automove writes correct value."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.set_automove(VogelsMotionMountAutoMoveType.Hdmi_1_On)
    mock_session.client.write_gatt_char.assert_called_once_with(
        CHAR_AUTOMOVE_UUID, (0).to_bytes(2, "big")
    )


@pytest.mark.asyncio
async def test_set_freeze_preset_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """set_freeze_preset writes the selected index when TV on/off detection permission is present."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.set_freeze_preset(2)
    mock_session.client.write_gatt_char.assert_awaited_once_with(
        CHAR_FREEZE_UUID, bytes([2])
    )


@pytest.mark.asyncio
async def test_set_multi_pin_features_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Set multi-pin features writes bitfield correctly."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    features = VogelsMotionMountMultiPinFeatures(
        change_presets=True,
        change_name=False,
        disable_channel=True,
        change_tv_on_off_detection=False,
        change_default_position=True,
        start_calibration=True,
    )
    await client.set_multi_pin_features(features)
    mock_session.client.write_gatt_char.assert_called_once()


@pytest.mark.asyncio
async def test_set_name_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Set name writes padded bytearray."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.set_name("MyMount")
    expected_bytes = bytearray(b"MyMount").ljust(20, b"\x00")
    mock_session.client.write_gatt_char.assert_called_once_with(
        CHAR_NAME_UUID, expected_bytes
    )


@pytest.mark.asyncio
async def test_set_preset_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """set_preset writes both preset and preset-name characteristics, padded to expected lengths."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    preset = VogelsMotionMountPreset(
        index=1,
        data=VogelsMotionMountPresetData(name="Room", distance=33, rotation=-12),
    )
    await client.set_preset(preset)
    assert mock_session.client.write_gatt_char.call_count == 2
    first_args, _ = mock_session.client.write_gatt_char.call_args_list[0]
    second_args, _ = mock_session.client.write_gatt_char.call_args_list[1]
    assert first_args[0] == CHAR_PRESET_UUIDS[preset.index]
    assert len(first_args[1]) == 20
    assert second_args[0] == CHAR_PRESET_NAMES_UUIDS[preset.index]
    assert len(second_args[1]) == 17


@pytest.mark.asyncio
async def test_set_preset_with_none_data_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """set_preset writes correct bytes when preset.data is None."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    preset = VogelsMotionMountPreset(index=0, data=None)
    await client.set_preset(preset)
    expected_data = bytes([0x00]).ljust(20, b"\x00")
    mock_session.client.write_gatt_char.assert_any_await(
        CHAR_PRESET_UUIDS[0], expected_data
    )
    mock_session.client.write_gatt_char.assert_any_await(
        CHAR_PRESET_NAMES_UUIDS[0], b"\x00" * 17
    )


@pytest.mark.asyncio
async def test_set_supervisior_pin_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """set_supervisior_pin writes encoded supervisor bytes when permissions allow."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.set_supervisior_pin("4321")
    mock_session.client.write_gatt_char.assert_awaited_once()
    args, _ = mock_session.client.write_gatt_char.call_args_list[0]
    assert args[0] == CHAR_CHANGE_PIN_UUID
    assert isinstance(args[1], (bytes, bytearray))
    assert len(args[1]) == 2


@pytest.mark.asyncio
async def test_set_tv_width_writes(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Set TV width writes correct byte."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    await client.set_tv_width(120)
    mock_session.client.write_gatt_char.assert_called_once_with(
        CHAR_WIDTH_UUID, bytes([120])
    )


# -------------------------------
# region Connection tests
# -------------------------------


@pytest.mark.asyncio
async def test_connect_is_singleton():
    """Multiple concurrent _connect calls result in a single connection attempt."""
    establish_connection = AsyncMock()

    with (
        patch(
            "custom_components.vogels_motion_mount_ble.client.establish_connection",
            establish_connection,
        ),
    ):
        client = VogelsMotionMountBluetoothClient(
            pin=None,
            device=AsyncMock(),
            permission_callback=lambda x: None,
            connection_callback=lambda x: None,
            distance_callback=lambda x: None,
            rotation_callback=lambda x: None,
        )

        # Act
        results = await asyncio.gather(
            client._connect(),  # noqa: SLF001
            client._connect(),  # noqa: SLF001
            client._connect(),  # noqa: SLF001
        )

        # Assert
        assert establish_connection.call_count == 1
        assert all(r is client._session_data for r in results)  # noqa: SLF001


@pytest.mark.asyncio
async def test_connect_returns_existing_session_data(
    mock_dev: BLEDevice, mock_session: _VogelsMotionMountSessionData
):
    """_connect returns existing session data if already connected."""
    client = VogelsMotionMountBluetoothClient(
        pin=1234,
        device=mock_dev,
        permission_callback=lambda p: None,
        connection_callback=lambda c: None,
        distance_callback=lambda d: None,
        rotation_callback=lambda r: None,
    )
    client._session_data = mock_session  # noqa: SLF001
    returned_session = await client._connect()  # noqa: SLF001
    assert returned_session is mock_session


@pytest.mark.asyncio
async def test_connect_sets_session_and_triggers_callbacks(mock_dev):
    """Ensure _connect sets session data, calls callbacks, and returns session."""
    mock_client = AsyncMock(spec=BleakClient)
    mock_perms = VogelsMotionMountPermissions(
        auth_status=VogelsMotionMountAuthenticationStatus(
            auth_type=VogelsMotionMountAuthenticationType.Full
        ),
        change_settings=True,
        change_default_position=True,
        change_name=True,
        change_presets=True,
        change_tv_on_off_detection=True,
        disable_channel=True,
        start_calibration=True,
    )
    with (
        patch(
            "custom_components.vogels_motion_mount_ble.client.establish_connection",
            return_value=mock_client,
        ),
        patch(
            "custom_components.vogels_motion_mount_ble.client.get_permissions",
            return_value=mock_perms,
        ),
    ):
        connection_cb = MagicMock()
        permission_cb = MagicMock()
        client = VogelsMotionMountBluetoothClient(
            pin=1234,
            device=mock_dev,
            permission_callback=permission_cb,
            connection_callback=connection_cb,
            distance_callback=lambda _: None,
            rotation_callback=lambda _: None,
        )
        session = await client._connect()  # noqa: SLF001
        assert isinstance(session, _VogelsMotionMountSessionData)
        permission_cb.assert_called_once_with(mock_perms)
        connection_cb.assert_called_once_with(mock_client.is_connected)


def test_handle_disconnect_resets_session_and_triggers_callback(mock_dev):
    """Ensure _handle_disconnect clears session and calls connection callback."""
    connection_cb = MagicMock()
    client = VogelsMotionMountBluetoothClient(
        pin=None,
        device=mock_dev,
        permission_callback=lambda _: None,
        connection_callback=connection_cb,
        distance_callback=lambda _: None,
        rotation_callback=lambda _: None,
    )
    client._session_data = MagicMock()  # noqa: SLF001
    client._handle_disconnect(MagicMock(spec=BleakClient))  # noqa: SLF001
    assert client._session_data is None  # noqa: SLF001
    connection_cb.assert_called_once_with(False)


# -------------------------------
# region Notifications tests
# -------------------------------


@pytest.mark.asyncio
async def test_setup_notifications_registers_distance_and_rotation(mock_dev):
    """Ensure _setup_notifications registers start_notify for distance and rotation."""
    mock_client = AsyncMock(spec=BleakClient)
    client = VogelsMotionMountBluetoothClient(
        pin=None,
        device=mock_dev,
        permission_callback=lambda _: None,
        connection_callback=lambda _: None,
        distance_callback=lambda _: None,
        rotation_callback=lambda _: None,
    )
    await client._setup_notifications(mock_client)  # noqa: SLF001
    assert mock_client.start_notify.await_count == 2


@pytest.mark.asyncio
async def test_distance_callback_fires(
    client: VogelsMotionMountBluetoothClient, callbacks
):
    """Distance callback is called when notification arrives."""
    client._handle_distance_change(None, (10).to_bytes(2, "big"))  # noqa: SLF001
    callbacks["distance"].assert_called_once_with(10)


@pytest.mark.asyncio
async def test_rotation_callback_fires(
    client: VogelsMotionMountBluetoothClient, callbacks
):
    """Rotation callback is called when notification arrives."""
    client._handle_rotation_change(None, (-20).to_bytes(2, "big", signed=True))  # noqa: SLF001
    callbacks["rotation"].assert_called_once_with(-20)


# -------------------------------
# region Permissions and errors
# -------------------------------


@pytest.mark.asyncio
async def test_write_without_permission_raises(
    client: VogelsMotionMountBluetoothClient,
    mock_session: _VogelsMotionMountSessionData,
):
    """Writing a characteristic without permission raises authentication error."""
    client._connect = AsyncMock(return_value=mock_session)  # noqa: SLF001
    mock_session.permissions = VogelsMotionMountPermissions(
        auth_status=None,
        change_name=False,
        change_presets=False,
        change_settings=False,
        change_tv_on_off_detection=False,
        disable_channel=False,
        change_default_position=False,
        start_calibration=False,
    )
    client._session_data = mock_session  # noqa: SLF001
    with pytest.raises(VogelsMotionMountClientAuthenticationError):
        await client._write(CHAR_NAME_UUID, b"test")  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_permissions_full_returns_all_true():
    """Ensure get_permissions returns all permissions True when auth is Full."""
    mock_client = AsyncMock()
    status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Full
    )
    with patch(
        "custom_components.vogels_motion_mount_ble.client._get_max_auth_status",
        return_value=status,
    ):
        perms = await get_permissions(mock_client, 1234)
        assert all(getattr(perms, f) for f in vars(perms) if f != "auth_status")


@pytest.mark.asyncio
async def test_get_permissions_control_reads_features():
    """Ensure get_permissions maps features correctly for Control auth type."""
    mock_client = AsyncMock()
    status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Control
    )
    features = VogelsMotionMountMultiPinFeatures(
        change_presets=True,
        change_name=False,
        disable_channel=True,
        change_tv_on_off_detection=False,
        change_default_position=True,
        start_calibration=False,
    )
    with (
        patch(
            "custom_components.vogels_motion_mount_ble.client._get_max_auth_status",
            return_value=status,
        ),
        patch(
            "custom_components.vogels_motion_mount_ble.client._read_multi_pin_features_directly",
            return_value=features,
        ),
    ):
        perms = await get_permissions(mock_client, 1234)
        assert perms.change_presets
        assert not perms.change_name
        assert perms.disable_channel
        assert perms.change_default_position


@pytest.mark.asyncio
async def test_get_permissions_wrong_returns_all_false():
    """Ensure get_permissions returns all permissions False when auth is Wrong."""
    mock_client = AsyncMock()
    status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Wrong
    )
    with patch(
        "custom_components.vogels_motion_mount_ble.client._get_max_auth_status",
        return_value=status,
    ):
        perms = await get_permissions(mock_client, 1234)
        assert not perms.change_settings
        assert not perms.change_presets
        assert perms.auth_status.auth_type == VogelsMotionMountAuthenticationType.Wrong


@pytest.mark.asyncio
async def test_get_max_auth_status_with_pin_supervisor_then_authorised():
    """Ensure _get_max_auth_status tries supervisor pin first, then authorised user."""
    mock_client = AsyncMock()
    # First call returns Wrong, second returns Control
    with patch(
        "custom_components.vogels_motion_mount_ble.client._get_auth_status",
        side_effect=[
            VogelsMotionMountAuthenticationStatus(
                auth_type=VogelsMotionMountAuthenticationType.Control
            ),
            VogelsMotionMountAuthenticationStatus(
                auth_type=VogelsMotionMountAuthenticationType.Full
            ),
        ],
    ):
        result = await _get_max_auth_status(mock_client, 1234)
        assert result.auth_type == VogelsMotionMountAuthenticationType.Control


@pytest.mark.asyncio
async def test_get_max_auth_status_supervisor_succeeds():
    """Supervisor authentication succeeds, only supervisor pin is written."""
    mock_client = AsyncMock()
    expected_status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Full
    )

    with patch(
        "custom_components.vogels_motion_mount_ble.client._get_auth_status",
        return_value=expected_status,
    ) as mock_get_auth:
        result = await _get_max_auth_status(mock_client, 9999)

    # Only supervisor pin written
    mock_client.write_gatt_char.assert_awaited_once()
    args, _ = mock_client.write_gatt_char.await_args
    assert args[0] == CHAR_AUTHENTICATE_UUID
    assert args[1] == _encode_supervisior_pin(9999)

    # Result is supervisor's auth status
    assert result == expected_status
    mock_get_auth.assert_awaited()


@pytest.mark.asyncio
async def test_get_max_auth_status_falls_back_to_authorised_user():
    """If supervisor pin fails (auth_type=Wrong), authorised user pin is tried."""
    mock_client = AsyncMock()

    # First call returns Wrong, second call returns Control
    first_status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Wrong
    )
    second_status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Control
    )

    with patch(
        "custom_components.vogels_motion_mount_ble.client._get_auth_status",
        side_effect=[first_status, second_status],
    ):
        result = await _get_max_auth_status(mock_client, 4321)

    # Both pins written
    assert mock_client.write_gatt_char.await_count == 2

    # First write is supervisor pin
    first_args, _ = mock_client.write_gatt_char.await_args_list[0]
    assert first_args[0] == CHAR_AUTHENTICATE_UUID
    assert first_args[1] == _encode_supervisior_pin(4321)

    # Second write is authorised user pin
    second_args, _ = mock_client.write_gatt_char.await_args_list[1]
    assert second_args[0] == CHAR_AUTHENTICATE_UUID
    assert second_args[1] == (4321).to_bytes(2, "little")

    # Result is second auth status
    assert result == second_status


@pytest.mark.asyncio
async def test_get_max_auth_status_without_pin():
    """Ensure _get_max_auth_status returns fallback status when no pin provided."""
    mock_client = AsyncMock()
    status = VogelsMotionMountAuthenticationStatus(
        auth_type=VogelsMotionMountAuthenticationType.Full
    )
    with patch(
        "custom_components.vogels_motion_mount_ble.client._get_auth_status",
        return_value=status,
    ):
        result = await _get_max_auth_status(mock_client, None)
        assert result.auth_type == VogelsMotionMountAuthenticationType.Full


@pytest.mark.asyncio
async def test_get_auth_status_full_control_wrong():
    """Ensure _get_auth_status decodes correct auth type from raw data."""
    mock_client = AsyncMock()

    # Full
    mock_client.read_gatt_char.return_value = b"\x80\x80\x00\x00"
    status = await _get_auth_status(mock_client)
    assert status.auth_type == VogelsMotionMountAuthenticationType.Full

    # Control
    mock_client.read_gatt_char.return_value = b"\x80\x00\x00"
    status = await _get_auth_status(mock_client)
    assert status.auth_type == VogelsMotionMountAuthenticationType.Control

    # Wrong → returns cooldown
    mock_client.read_gatt_char.return_value = b"\x01\x00\x00\x00"
    status = await _get_auth_status(mock_client)
    assert status.auth_type == VogelsMotionMountAuthenticationType.Wrong
    assert status.cooldown is not None


@pytest.mark.asyncio
async def test_read_multi_pin_features_directly_maps_bits():
    """Ensure _read_multi_pin_features_directly maps bitflags to correct features."""
    mock_client = AsyncMock()
    # Binary mask: bits 0,2,4 set → change_presets, disable_channel, change_default_position
    mock_client.read_gatt_char.return_value = bytes([0b00010101])
    result = await _read_multi_pin_features_directly(mock_client)
    assert result.change_presets
    assert result.disable_channel
    assert result.change_default_position
    assert not result.change_name
    assert not result.change_tv_on_off_detection
