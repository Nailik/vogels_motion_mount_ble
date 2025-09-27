"""Fixtures for testing."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from bleak.backends.device import BLEDevice
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vogels_motion_mount_ble import VogelsMotionMountBleCoordinator
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
    VogelsMotionMountVersions,
)
from homeassistant.core import HomeAssistant

DOMAIN = "vogels_motion_mount_ble"
MOCKED_CONF_ENTRY_ID = "some-entry-id"
MOCKED_CONF_ENTRY_UNIQUE_ID = "some-entry-unique-id"
MOCKED_CONF_DEVICE_ID = "some-device-id"
MOCKED_CONF_MAC = "AA:BB:CC:DD:EE:FF"
MOCKED_CONF_NAME = "Mount"
MOCKED_CONF_PIN = 1234
CONF_MAC = "conf_mac"
CONF_NAME = "conf_name"
CONF_PIN = "conf_pin"
CONF_ERROR = "base"
MIN_HA_VERSION = "2025.6.0"

MOCKED_CONFIG: dict[str, Any] = {
    CONF_MAC: MOCKED_CONF_MAC,
    CONF_NAME: MOCKED_CONF_NAME,
    CONF_PIN: MOCKED_CONF_PIN,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in HA for tests."""
    return


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth):
    """Mock bluetooth."""
    return


async def setup_integration(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Fixture for setting up the component."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture(autouse=True)
def mock_coord(mock_data: MagicMock):
    """Mock the coordinator with custom data."""
    with patch(
        "custom_components.vogels_motion_mount_ble.VogelsMotionMountBleCoordinator"
    ) as mock_coord:
        instance = MagicMock(spec=VogelsMotionMountBleCoordinator)
        instance.address = MOCKED_CONF_MAC
        instance.name = MOCKED_CONF_NAME
        instance._read_data = AsyncMock()  # noqa: SLF001
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
        instance._async_update_data = AsyncMock()  # noqa: SLF001
        instance.last_update_success = True
        mock_coord.return_value = instance
        yield instance


@pytest.fixture(autouse=True)
def mock_config_entry(mock_coord: MagicMock, hass: HomeAssistant):
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
def mock_conn():
    """Mock establishing a bluetooth connection."""
    with patch(
        "bleak_retry_connector.establish_connection", new_callable=AsyncMock
    ) as mock_conn:
        mock_conn.return_value = AsyncMock()
        yield mock_conn


@pytest.fixture(autouse=True)
def mock_data():
    """Mock full data set."""
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
    """Mock a found bluetooth device."""
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_dev:
        mock_dev.return_value = BLEDevice(
            address=MOCKED_CONF_MAC,
            name=MOCKED_CONF_NAME,
            details={},
        )
        yield mock_dev
