"""Tests for the coordinator."""

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

from bleak.backends.device import BLEDevice
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vogels_motion_mount_ble.client import (
    VogelsMotionMountBluetoothClient,
)
from custom_components.vogels_motion_mount_ble.coordinator import (
    VogelsMotionMountBleCoordinator,
)
from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountAuthenticationStatus,
    VogelsMotionMountAuthenticationType,
    VogelsMotionMountAutoMoveType,
    VogelsMotionMountData,
    VogelsMotionMountMultiPinFeatures,
    VogelsMotionMountPermissions,
    VogelsMotionMountPinSettings,
    VogelsMotionMountPreset,
    VogelsMotionMountPresetData,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ServiceValidationError
from homeassistant.helpers.update_coordinator import UpdateFailed


# Example fixtures (already split)
@pytest.fixture
async def mock_client() -> VogelsMotionMountBluetoothClient:
    """Mock the bluetooth client interface."""
    client = AsyncMock()
    client.read_distance.return_value = 10
    client.read_rotation.return_value = 20
    client.read_name.return_value = "Vogel"
    client.read_tv_width.return_value = 55
    client.read_pin_settings.return_value = VogelsMotionMountPinSettings.Deactivated
    client.read_automove.return_value = VogelsMotionMountAutoMoveType.Hdmi_1_Off
    client.read_presets.return_value = []
    client.read_permissions.return_value = VogelsMotionMountPermissions(
        auth_status=None,
        change_settings=True,
        change_default_position=True,
        change_name=True,
        change_presets=True,
        change_tv_on_off_detection=True,
        disable_channel=True,
        start_calibration=True,
    )
    client.read_multi_pin_features.return_value = VogelsMotionMountMultiPinFeatures(
        change_default_position=True,
        change_name=True,
        change_presets=True,
        change_tv_on_off_detection=True,
        disable_channel=True,
        start_calibration=True,
    )
    client.read_freeze_preset_index.return_value = 0
    client.read_versions.return_value = None
    return client


@pytest.fixture
async def coordinator(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_bledevice: BLEDevice,
    mock_client: AsyncMock,
    mock_data: VogelsMotionMountData,
):
    """Real coordinator with injected mock client."""
    coordinator = VogelsMotionMountBleCoordinator(
        hass=hass,
        config_entry=mock_config_entry,
        device=mock_bledevice,
        unsub_options_update_listener=lambda: None,
    )
    coordinator.data = mock_data
    coordinator._client = mock_client  # noqa: SLF001
    return coordinator


# -----------------------------
# region Setup
# -----------------------------


@pytest.mark.asyncio
async def test_available_and_unavailable_callbacks(
    coordinator: VogelsMotionMountBleCoordinator,
):
    """Test availability callbacks."""
    # Device becomes available
    assert coordinator.data.available

    coordinator._unavailable_callback(MagicMock())  # noqa: SLF001
    assert not coordinator.data.available

    coordinator._available_callback(MagicMock(), MagicMock())  # noqa: SLF001
    assert coordinator.data.available


@pytest.mark.asyncio
async def test_available_and_unavailable_callbacks_without_data(
    coordinator: VogelsMotionMountBleCoordinator,
):
    """Test availability callbacks."""
    # Device becomes available
    coordinator.data = None
    assert not coordinator.data

    coordinator._unavailable_callback(MagicMock())  # noqa: SLF001
    coordinator._available_callback(MagicMock(), MagicMock())  # noqa: SLF001


@pytest.mark.asyncio
async def test_unload(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test unloading of coordinator."""
    unsub_called = False
    unsub_unavailable_called = False
    unsub_available_called = False

    def unsub():
        nonlocal unsub_called
        unsub_called = True

    def unsub_unavailable():
        nonlocal unsub_unavailable_called
        unsub_unavailable_called = True

    def unsub_available():
        nonlocal unsub_available_called
        unsub_available_called = True

    coordinator._unsub_options_update_listener = unsub  # noqa: SLF001
    coordinator._unsub_unavailable_update_listener = unsub_unavailable  # noqa: SLF001
    coordinator._unsub_available_update_listener = unsub_available  # noqa: SLF001

    await coordinator.unload()
    mock_client.disconnect.assert_awaited()
    assert unsub_called
    assert unsub_unavailable
    assert unsub_available


@pytest.mark.asyncio
async def test_refresh_data(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test refresh data action."""
    await coordinator.refresh_data()
    mock_client.read_distance.assert_awaited()


# -----------------------------
# region Control
# -----------------------------


@pytest.mark.asyncio
async def test_select_preset(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test select preset action."""
    await coordinator.select_preset(3)
    mock_client.select_preset.assert_awaited_with(3)


@pytest.mark.asyncio
async def test_start_calibration(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test start calibtration action."""
    await coordinator.start_calibration()
    mock_client.start_calibration.assert_awaited()


# -----------------------------
# region Config
# -----------------------------


@pytest.mark.asyncio
async def test_request_distance(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test requesting distance."""
    await coordinator.request_distance(42)
    mock_client.request_distance.assert_awaited_once_with(42)
    assert coordinator.data.requested_distance == 42


@pytest.mark.asyncio
async def test_request_rotation(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test requesting rotation."""
    await coordinator.request_rotation(15)
    mock_client.request_rotation.assert_awaited_once_with(15)
    assert coordinator.data.requested_rotation == 15


@pytest.mark.asyncio
async def test_set_authorised_user_pin_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting authorised user pin."""
    mock_client.read_pin_settings.return_value = VogelsMotionMountPinSettings.Single
    await coordinator.set_authorised_user_pin("1234")
    mock_client.set_authorised_user_pin.assert_awaited_once_with("1234")


@pytest.mark.asyncio
async def test_set_authorised_user_pin_failure(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test failure setting authorised user pin."""
    mock_client.read_pin_settings.return_value = (
        VogelsMotionMountPinSettings.Deactivated
    )
    with pytest.raises(ServiceValidationError):
        await coordinator.set_authorised_user_pin("1234")


@pytest.mark.asyncio
async def test_set_automove_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting automove type."""
    mock_client.read_automove.return_value = VogelsMotionMountAutoMoveType.Hdmi_2_On
    await coordinator.set_automove(VogelsMotionMountAutoMoveType.Hdmi_2_On)
    mock_client.set_automove.assert_awaited_once_with(
        VogelsMotionMountAutoMoveType.Hdmi_2_On
    )
    assert coordinator.data.automove == VogelsMotionMountAutoMoveType.Hdmi_2_On


@pytest.mark.asyncio
async def test_set_automove_failure(
    coordinator: VogelsMotionMountBleCoordinator, mock_client
):
    """Test failure setting automove type."""
    target = VogelsMotionMountAutoMoveType(0)
    mock_client.read_automove.return_value = VogelsMotionMountAutoMoveType(8)
    with pytest.raises(ServiceValidationError):
        await coordinator.set_automove(target)


@pytest.mark.asyncio
async def test_set_freeze_preset_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting freeze preset index."""
    mock_client.read_freeze_preset_index.return_value = 2
    await coordinator.set_freeze_preset(2)
    mock_client.set_freeze_preset.assert_awaited_with(2)
    assert coordinator.data.freeze_preset_index == 2


@pytest.mark.asyncio
async def test_set_freeze_preset_failure(
    coordinator: VogelsMotionMountBleCoordinator, mock_client
):
    """Test failure setting freeze preset index."""
    mock_client.read_freeze_preset_index.return_value = 9
    with pytest.raises(ServiceValidationError):
        await coordinator.set_freeze_preset(1)


@pytest.mark.asyncio
async def test_set_multi_pin_features_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting multi pin features."""
    new_features = replace(coordinator.data.multi_pin_features, change_name=False)
    mock_client.read_multi_pin_features.return_value = new_features
    await coordinator.set_multi_pin_features(new_features)
    mock_client.set_multi_pin_features.assert_awaited_with(new_features)
    assert coordinator.data.multi_pin_features.change_name is False


@pytest.mark.asyncio
async def test_set_multi_pin_features_failure(
    coordinator: VogelsMotionMountBleCoordinator, mock_client
):
    """Test failure setting multi pin features."""
    features = replace(coordinator.data.multi_pin_features, change_presets=True)
    mock_client.read_multi_pin_features.return_value = replace(
        features, change_presets=False
    )
    with pytest.raises(ServiceValidationError):
        await coordinator.set_multi_pin_features(features)


@pytest.mark.asyncio
async def test_set_name_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting name."""
    mock_client.read_name.return_value = "NewName"
    await coordinator.set_name("NewName")
    mock_client.set_name.assert_awaited_once_with("NewName")
    assert coordinator.data.name == "NewName"


@pytest.mark.asyncio
async def test_set_name_failure(
    coordinator: VogelsMotionMountBleCoordinator, mock_client
):
    """Test failure setting name."""
    coordinator.data = replace(coordinator.data, name="Old")
    mock_client.read_name.return_value = "Wrong"
    with pytest.raises(ServiceValidationError):
        await coordinator.set_name("New")


@pytest.mark.asyncio
async def test_set_preset_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting preset data."""
    preset = VogelsMotionMountPreset(
        index=1,
        data=VogelsMotionMountPresetData(name="somename", distance=10, rotation=50),
    )
    mock_client.read_preset.return_value = preset
    await coordinator.set_preset(preset)
    mock_client.set_preset.assert_awaited_with(preset)
    assert coordinator.data.presets[1] == preset


@pytest.mark.asyncio
async def test_set_preset_failure(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test failure setting preset data."""
    preset = VogelsMotionMountPreset(
        index=0,
        data=VogelsMotionMountPresetData(name="somename", distance=10, rotation=50),
    )
    preset_mismatch = VogelsMotionMountPreset(
        index=0,
        data=VogelsMotionMountPresetData(name="somenae", distance=1, rotation=5),
    )
    mock_client.read_preset.return_value = preset_mismatch
    with pytest.raises(ServiceValidationError):
        await coordinator.set_preset(preset)


@pytest.mark.asyncio
async def test_set_supervisior_pin_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting supervisior pin."""
    mock_client.read_pin_settings.return_value = VogelsMotionMountPinSettings.Multi
    await coordinator.set_supervisior_pin("5678")
    mock_client.set_supervisior_pin.assert_awaited_once_with("5678")


@pytest.mark.asyncio
async def test_set_supervisior_pin_failure(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test failure setting supervisior pin."""
    mock_client.read_pin_settings.return_value = (
        VogelsMotionMountPinSettings.Deactivated
    )
    with pytest.raises(ServiceValidationError):
        await coordinator.set_supervisior_pin("5678")


@pytest.mark.asyncio
async def test_set_tv_width_success(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test successful setting tv width."""
    mock_client.read_tv_width.return_value = 100
    await coordinator.set_tv_width(100)
    mock_client.set_tv_width.assert_awaited_once_with(100)
    assert coordinator.data.tv_width == 100


@pytest.mark.asyncio
async def test_set_tv_width_failure(
    coordinator: VogelsMotionMountBleCoordinator,
    mock_client: VogelsMotionMountBluetoothClient,
):
    """Test failure setting tv width."""
    coordinator.data = replace(coordinator.data, tv_width=100)
    mock_client.read_tv_width.return_value = 999
    with pytest.raises(ServiceValidationError):
        await coordinator.set_tv_width(200)


# -----------------------------
# region Notifications
# -----------------------------


def test_permissions_changed(coordinator: VogelsMotionMountBleCoordinator):
    """Test permission change callback."""
    new_perm = replace(coordinator.data.permissions, change_name=False)
    coordinator._permissions_changed(new_perm)  # noqa: SLF001
    assert coordinator.data.permissions.change_name is False


def test_connection_changed(coordinator: VogelsMotionMountBleCoordinator):
    """Test connection change callback."""
    coordinator._connection_changed(True)  # noqa: SLF001
    assert coordinator.data.connected is True


def test_distance_changed(coordinator: VogelsMotionMountBleCoordinator):
    """Test permission change callback."""
    coordinator._distance_changed(42)  # noqa: SLF001
    assert coordinator.data.distance == 42


def test_rotation_changed(coordinator: VogelsMotionMountBleCoordinator):
    """Test rotation change callback."""
    coordinator._rotation_changed(90)  # noqa: SLF001
    assert coordinator.data.rotation == 90


# -------------------------------
# region internal
# -------------------------------


@pytest.mark.asyncio
async def test_async_update_data_propagates_entryauthfailed_on_exception(
    coordinator: VogelsMotionMountBleCoordinator,
):
    """Check async update data throws UpdateFailed on exception."""
    coordinator._client.read_permissions.side_effect = ConfigEntryAuthFailed("boom")  # noqa: SLF001

    with pytest.raises(ConfigEntryAuthFailed, match="boom"):
        await coordinator._async_update_data()  # noqa: SLF001


@pytest.mark.asyncio
async def test_async_update_data_raises_updatefailed_on_exception(
    coordinator: VogelsMotionMountBleCoordinator,
):
    """Check async update data throws UpdateFailed on exception."""
    coordinator._client.read_permissions.side_effect = RuntimeError("boom")  # noqa: SLF001

    with pytest.raises(UpdateFailed, match="boom"):
        await coordinator._async_update_data()  # noqa: SLF001


@pytest.mark.asyncio
async def test_check_permission_status_raises_error(
    coordinator: VogelsMotionMountBleCoordinator,
):
    """It should raise ConfigEntryAuthFailed when auth_type is Wrong."""
    permissions = VogelsMotionMountPermissions(
        auth_status=VogelsMotionMountAuthenticationStatus(
            auth_type=VogelsMotionMountAuthenticationType.Wrong
        ),
        change_settings=False,
        change_default_position=False,
        change_name=False,
        change_presets=False,
        change_tv_on_off_detection=False,
        disable_channel=False,
        start_calibration=False,
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._check_permission_status(permissions)  # noqa: SLF001
