"""Fixtures for testing."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest.mock import AsyncMock, patch, MagicMock
from . import (
    MOCKED_CONF_ENTRY_ID,
    MOCKED_CONF_ENTRY_UNIQUE_ID,
    MOCKED_CONFIG,
    DOMAIN,
    MOCKED_CONF_MAC,
    MOCKED_CONF_NAME,
    MOCKED_CONF_DEVICE_ID,
)
from homeassistant.core import HomeAssistant

from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountAuthenticationType,
    VogelsMotionMountPermissions,
    VogelsMotionMountAuthenticationStatus,
    VogelsMotionMountPreset,
    VogelsMotionMountData,
    VogelsMotionMountAutoMoveType,
    VogelsMotionMountMultiPinFeatures,
    VogelsMotionMountPinSettings,
    VogelsMotionMountPresetData,
    VogelsMotionMountVersions,
)
from custom_components.vogels_motion_mount_ble import VogelsMotionMountBleCoordinator


@pytest.fixture(autouse=True)
def mock_coord(mock_data: MagicMock):
    with patch(
        "custom_components.vogels_motion_mount_ble.VogelsMotionMountBleCoordinator"
    ) as mock_coord:
        instance = MagicMock(spec=VogelsMotionMountBleCoordinator)
        instance.address = MOCKED_CONF_MAC
        instance.name = MOCKED_CONF_NAME
        instance._read_data = AsyncMock()
        instance.async_config_entry_first_refresh = AsyncMock()
        instance.unload = AsyncMock()
        instance.data = mock_data
        instance.start_calibration = AsyncMock()
        instance.refresh_data = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.select_preset = AsyncMock()
        instance.set_preset = AsyncMock()
        instance.set_tv_width = AsyncMock()
        instance.set_rotation = AsyncMock()
        instance.set_distance = AsyncMock()
        instance.set_authorised_user_pin = AsyncMock()
        instance._async_update_data = AsyncMock()
        mock_coord.return_value = instance
        yield instance


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth):
    yield


@pytest.fixture(autouse=True)
def mock_config_entry(mock_coord: MagicMock, hass: HomeAssistant) -> MockConfigEntry:
    """Mock a config entry."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="VogelsMotionMount",
        data=MOCKED_CONFIG,
        unique_id=MOCKED_CONF_ENTRY_UNIQUE_ID,
        entry_id=MOCKED_CONF_ENTRY_ID,
    )
    mock_config_entry.runtime_data = mock_coord
    mock_config_entry.add_to_hass(hass)
    return mock_config_entry


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return enable_custom_integrations


@pytest.fixture(autouse=True)
def mock_conn():
    with patch(
        "bleak_retry_connector.establish_connection", new_callable=AsyncMock
    ) as mock_conn:
        mock_conn.return_value = AsyncMock()
        yield mock_conn


@pytest.fixture(autouse=True)
def mock_data():
    with patch(
        "custom_components.vogels_motion_mount_ble.data.VogelsMotionMountData"
    ) as mock_data:
        instance = VogelsMotionMountData(
            automove=VogelsMotionMountAutoMoveType.Hdmi_1_On,
            connected=True,
            distance=100,
            freeze_preset_index=0,
            multi_pin_features=VogelsMotionMountMultiPinFeatures(
                change_default_position=True,
                change_name=True,
                change_presets=True,
                change_tv_on_off_detection=False,
                disable_channel=False,
                start_calibration=True,
            ),
            name="Living Room Mount",
            pin_setting=VogelsMotionMountPinSettings.Single,
            presets=[
                VogelsMotionMountPreset(
                    index=0,
                    data=VogelsMotionMountPresetData(
                        distance=80,
                        name="Movie Mode",
                        rotation=15,
                    ),
                ),
                VogelsMotionMountPreset(
                    index=1,
                    data=VogelsMotionMountPresetData(
                        distance=80,
                        name="Movie Mode",
                        rotation=15,
                    ),
                ),
                VogelsMotionMountPreset(
                    index=2,
                    data=VogelsMotionMountPresetData(
                        distance=80,
                        name="Movie Mode",
                        rotation=15,
                    ),
                ),
                VogelsMotionMountPreset(
                    index=3,
                    data=VogelsMotionMountPresetData(
                        distance=100,
                        name="Gaming Mode",
                        rotation=-10,
                    ),
                ),
                VogelsMotionMountPreset(
                    index=4,
                    data=VogelsMotionMountPresetData(
                        distance=80,
                        name="Movie Mode",
                        rotation=15,
                    ),
                ),
                VogelsMotionMountPreset(
                    index=5,
                    data=VogelsMotionMountPresetData(
                        distance=80,
                        name="Movie Mode",
                        rotation=15,
                    ),
                ),
                VogelsMotionMountPreset(
                    index=6,
                    data=VogelsMotionMountPresetData(
                        distance=80,
                        name="Movie Mode",
                        rotation=15,
                    ),
                ),
            ],
            rotation=5,
            tv_width=140,
            versions=VogelsMotionMountVersions(
                ceb_bl_version="1.0.0",
                mcp_bl_version="1.0.1",
                mcp_fw_version="2.0.0",
                mcp_hw_version="revA",
            ),
            permissions=VogelsMotionMountPermissions(
                auth_status=VogelsMotionMountAuthenticationStatus(
                    auth_type=VogelsMotionMountAuthenticationType.Full,
                    cooldown=None,
                ),
                change_settings=True,
                change_default_position=True,
                change_name=True,
                change_presets=True,
                change_tv_on_off_detection=True,
                disable_channel=False,
                start_calibration=True,
            ),
            requested_distance=None,
            requested_rotation=None,
        )
        mock_data.return_value = instance
        yield instance


@pytest.fixture(autouse=True)
def mock_dev():
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_dev:
        mock_dev.return_value = MagicMock(
            address=MOCKED_CONF_MAC, name=MOCKED_CONF_NAME, details={}
        )
        yield mock_dev


@pytest.fixture(autouse=True)
def mock_device():
    with patch(
        "homeassistant.helpers.device_registry.DeviceRegistry.async_get"
    ) as mock_async_get:
        device = MagicMock()
        device.config_entries = {MOCKED_CONF_ENTRY_ID}

        def _side_effect(device_id: str):
            if device_id == MOCKED_CONF_DEVICE_ID:
                return device
            return None

        mock_async_get.side_effect = _side_effect
        yield mock_async_get
