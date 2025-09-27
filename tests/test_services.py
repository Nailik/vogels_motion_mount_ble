"""Tests for service setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.vogels_motion_mount_ble import services
from custom_components.vogels_motion_mount_ble.services import (
    DOMAIN,
    HA_SERVICE_DEVICE_ID,
    HA_SERVICE_PIN_ID,
    HA_SERVICE_SET_AUTHORISED_USER_PIN,
    HA_SERVICE_SET_SUPERVISIOR_PIN,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import NoEntitySpecifiedError

from .conftest import MOCKED_CONF_DEVICE_ID, MOCKED_CONF_ENTRY_ID  # noqa: TID251


@pytest.fixture(autouse=True)
def mock_device():
    """Mock the device from device registry."""
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


# -------------------------------
# region Setup
# -------------------------------


def test_services_registered(hass: HomeAssistant):
    """Test services registered correctly."""
    # Patch async_register so we can spy on calls

    services.async_setup_services(hass)

    # `async_services` is a dict keyed by domain
    domain_services = hass.services.async_services().get(DOMAIN)
    assert domain_services is not None

    # Check that our services exist
    assert HA_SERVICE_SET_AUTHORISED_USER_PIN in domain_services
    assert HA_SERVICE_SET_SUPERVISIOR_PIN in domain_services


# -------------------------------
# region Success
# -------------------------------


@pytest.mark.asyncio
async def test_set_authorised_user_pin_success(
    hass: HomeAssistant, mock_config_entry: AsyncMock
):
    """Test set authorised user pin calls correctly."""
    call = ServiceCall(
        domain=DOMAIN,
        service=HA_SERVICE_SET_AUTHORISED_USER_PIN,
        data={HA_SERVICE_DEVICE_ID: MOCKED_CONF_DEVICE_ID, HA_SERVICE_PIN_ID: "1111"},
        hass=hass,
    )

    await services._set_authorised_user_pin(call)  # noqa: SLF001
    mock_config_entry.runtime_data.set_authorised_user_pin.assert_awaited_once_with(
        "1111"
    )


@pytest.mark.asyncio
async def test_set_supervisior_pin_success(
    hass: HomeAssistant, mock_config_entry: AsyncMock
):
    """Test set supervisior pin calls correctly."""
    call = ServiceCall(
        domain=DOMAIN,
        service=HA_SERVICE_SET_SUPERVISIOR_PIN,
        data={HA_SERVICE_DEVICE_ID: MOCKED_CONF_DEVICE_ID, HA_SERVICE_PIN_ID: "2222"},
        hass=hass,
    )

    await services._set_supervisior_pin(call)  # noqa: SLF001
    mock_config_entry.runtime_data.set_supervisior_pin.assert_awaited_once_with("2222")


# -------------------------------
# region Coordinator
# -------------------------------


@pytest.mark.asyncio
async def test_get_coordinator_missing_device_id_raises(hass: HomeAssistant):
    """Test missing device id."""
    call = ServiceCall(
        domain=DOMAIN,
        service=HA_SERVICE_SET_AUTHORISED_USER_PIN,
        data={},
        hass=hass,
    )
    with pytest.raises(NoEntitySpecifiedError):
        services._get_coordinator(call)  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_coordinator_invalid_device_raises(hass: HomeAssistant):
    """Test invalid device id."""
    call = ServiceCall(
        domain=DOMAIN,
        service=HA_SERVICE_SET_AUTHORISED_USER_PIN,
        data={HA_SERVICE_DEVICE_ID: "sdrf"},
        hass=hass,
    )
    with pytest.raises(NoEntitySpecifiedError):
        services._get_coordinator(call)  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_coordinator_invalid_entry_raises(hass: HomeAssistant):
    """Test missing entry in device."""
    hass.config_entries.async_get_entry = MagicMock(return_value=None)
    hass.config_entries.async_unload = AsyncMock()

    call = ServiceCall(
        domain=DOMAIN,
        service=HA_SERVICE_SET_AUTHORISED_USER_PIN,
        data={HA_SERVICE_DEVICE_ID: MOCKED_CONF_DEVICE_ID},
        hass=hass,
    )
    with pytest.raises(NoEntitySpecifiedError):
        services._get_coordinator(call)  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_coordinator_invalid_runtime_data_raises(
    hass: HomeAssistant, mock_config_entry: AsyncMock
):
    """Test invalid device id."""
    hass.config_entries.async_get_entry = MagicMock(return_value=mock_config_entry)
    mock_config_entry.runtime_data = None

    call = ServiceCall(
        domain=DOMAIN,
        service=HA_SERVICE_SET_AUTHORISED_USER_PIN,
        data={HA_SERVICE_DEVICE_ID: MOCKED_CONF_DEVICE_ID},
        hass=hass,
    )
    with pytest.raises(NoEntitySpecifiedError):
        services._get_coordinator(call)  # noqa: SLF001
