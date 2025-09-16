import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import data_entry_flow
from homeassistant.config_entries import (
    SOURCE_USER,
    SOURCE_BLUETOOTH,
    SOURCE_REAUTH,
    SOURCE_RECONFIGURE,
)

from custom_components.vogels_motion_mount_ble.const import (
    DOMAIN,
    CONF_MAC,
    CONF_NAME,
    CONF_PIN,
    CONF_ERROR,
)
from custom_components.vogels_motion_mount_ble.api import (
    APIAuthenticationError,
    APIConnectionError,
    APIConnectionDeviceNotFoundError,
)


@pytest.fixture
def mock_api():
    with patch(
        "custom_components.vogels_motion_mount_ble.config_flow.API", autospec=True
    ) as mock_api:
        yield mock_api


async def test_user_flow_success(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "My Mount", CONF_PIN: 1234},
    )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "My Mount"
    assert result2["data"][CONF_MAC] == "AA:BB:CC:DD:EE:FF"


async def test_user_flow_invalid_mac(hass, mock_api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "INVALID-MAC", CONF_NAME: "Bad Mount"},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"][CONF_ERROR] == "invalid_mac_code"


async def test_user_flow_authentication_error(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(
        side_effect=APIAuthenticationError("bad pin", cooldown=0)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Mount", CONF_PIN: 9999},
    )

    assert result2["errors"][CONF_ERROR] == "error_invalid_authentication"


async def test_user_flow_authentication_cooldown(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(
        side_effect=APIAuthenticationError("cooldown", cooldown=30)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Mount"},
    )

    assert result2["errors"][CONF_ERROR] == "error_auth_cooldown"
    assert "cooldown" in result2["description_placeholders"]


async def test_user_flow_device_not_found(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(
        side_effect=APIConnectionDeviceNotFoundError("not found")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Mount"},
    )
    assert result2["errors"][CONF_ERROR] == "error_device_not_found"


async def test_user_flow_connection_error(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(
        side_effect=APIConnectionError("cannot connect")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Mount"},
    )
    assert result2["errors"][CONF_ERROR] == "error_cannot_connect"


async def test_user_flow_unknown_error(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(side_effect=Exception("boom"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Mount"},
    )
    assert result2["errors"][CONF_ERROR] == "error_unknown"


async def test_bluetooth_flow_creates_entry(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)

    discovery_info = type("d", (), {"address": "11:22:33:44:55:66"})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=discovery_info
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_reauth_flow(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)
    entry = hass.config_entries.async_entries(DOMAIN)
    assert entry == []

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": "1234"},
        data={CONF_MAC: "AA:BB:CC:DD:EE:FF"},
    )
    assert result["type2"] == data_entry_flow.RESULT_TYPE_FORM


async def test_reconfigure_flow(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)
    entry = hass.config_entries.async_entries(DOMAIN)
    assert entry == []

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": "1234"},
        data={CONF_MAC: "AA:BB:CC:DD:EE:FF"},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
