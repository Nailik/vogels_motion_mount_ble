"""Fixtures for testing."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest.mock import AsyncMock, patch, MagicMock
from . import (
    MOCKED_CONF_ENTRY_ID,
    MOCKED_CONFIG,
    DOMAIN,
    MOCKED_CONF_MAC,
    MOCKED_CONF_NAME,
)

from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountAuthenticationType,
    VogelsMotionMountPermissions,
    VogelsMotionMountAuthenticationStatus,
    VogelsMotionMountPreset,
)


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth):
    yield


@pytest.fixture(autouse=True)
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="VogelsMotionMount",
        data=MOCKED_CONFIG,
        unique_id=MOCKED_CONF_ENTRY_ID,
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture(autouse=True)
def mock_conn():
    with patch(
        "bleak_retry_connector.establish_connection", new_callable=AsyncMock
    ) as mock_conn:
        mock_conn.return_value = AsyncMock()
        yield mock_conn


@pytest.fixture(autouse=True)
def mock_async_update_data():
    with patch(
        "custom_components.vogels_motion_mount_ble.VogelsMotionMountBleCoordinator._async_update_data",
        new_callable=AsyncMock,
    ):
        yield


@pytest.fixture(autouse=True)
def mock_data():
    with patch(
        "custom_components.vogels_motion_mount_ble.VogelsMotionMountBleCoordinator"
    ) as mock_data:
        instance = MagicMock()
        instance.async_config_entry_first_refresh = AsyncMock()
        instance.address = MOCKED_CONF_MAC
        instance.name = MOCKED_CONF_NAME
        instance.data.name = MOCKED_CONF_NAME
        instance.data.presets = [
            VogelsMotionMountPreset(0, None),
            VogelsMotionMountPreset(1, None),
            VogelsMotionMountPreset(2, None),
            VogelsMotionMountPreset(3, None),
            VogelsMotionMountPreset(4, None),
            VogelsMotionMountPreset(5, None),
            VogelsMotionMountPreset(6, None),
        ]
        instance.data.permissions = VogelsMotionMountPermissions(
            auth_status=VogelsMotionMountAuthenticationStatus(
                auth_type=VogelsMotionMountAuthenticationType.Full,
            ),
            change_settings=True,
            change_default_position=True,
            change_name=True,
            change_presets=True,
            change_tv_on_off_detection=True,
            disable_channel=True,
            start_calibration=True,
        )
        mock_data.return_value = instance
        yield instance


@pytest.fixture(autouse=True)
def mock_dev(request):
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_dev:
        mock_dev.return_value = MagicMock(
            address=MOCKED_CONF_MAC, name=MOCKED_CONF_NAME, details={}
        )
        yield mock_dev
