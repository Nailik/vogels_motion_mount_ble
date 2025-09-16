"""Test component setup."""

from homeassistant.setup import async_setup_component
import pytest
from unittest.mock import patch
from custom_components.vogels_motion_mount_ble.const import DOMAIN


@pytest.fixture(autouse=True)
def patch_bluetooth_and_api():
    with patch(
        "homeassistant.components.bluetooth.BluetoothServiceInfoBleak"
    ) as mock_ble_info, patch(
        "homeassistant.components.bluetooth.async_setup",
        return_value=True,
    ):
        # Optionally provide default attributes for the BluetoothServiceInfoBleak mock
        mock_ble_info.return_value.address = "AA:BB:CC:DD:EE:FF"
        mock_ble_info.return_value.name = "Mock Device"

        yield


async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True
