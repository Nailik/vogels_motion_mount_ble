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
def mock_dev():
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_dev:
        mock_dev.return_value = MagicMock(
            address=MOCKED_CONF_MAC, name=MOCKED_CONF_NAME, details={}
        )
        yield mock_dev


@pytest.fixture(autouse=True)
def mock_coord():
    with patch(
        "custom_components.vogels_motion_mount_ble.VogelsMotionMountBleCoordinator"
    ) as mock_coord:
        instance = MagicMock()
        instance.async_config_entry_first_refresh = AsyncMock()
        mock_coord.return_value = instance
        yield instance
