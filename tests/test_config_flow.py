import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.data_entry_flow import FlowResultType
from custom_components.vogels_motion_mount_ble.api import APIAuthenticationError
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from typing import Any, Dict
from custom_components.vogels_motion_mount_ble.api import API
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from homeassistant.helpers.selector import (
    NumberSelector,
    TextSelector,
)
from homeassistant.config_entries import (
    SOURCE_USER,
    SOURCE_BLUETOOTH,
    SOURCE_REAUTH,
    SOURCE_RECONFIGURE,
)
import voluptuous as vol

from homeassistant.config_entries import UnknownEntry
from custom_components.vogels_motion_mount_ble.const import (
    DOMAIN,
    CONF_MAC,
    CONF_NAME,
    CONF_PIN,
    CONF_ERROR,
)
from custom_components.vogels_motion_mount_ble.api import (
    APIConnectionError,
    APIConnectionDeviceNotFoundError,
)
from unittest.mock import create_autospec

MOCKED_CONF_MAC = "AA:BB:CC:DD:EE:FF"
MOCKED_CONF_NAME = "Mount"
MOCKED_CONF_PIN = 1234

MOCKED_CONFIG: Dict[str, Any] = {
    CONF_MAC: MOCKED_CONF_MAC,
    CONF_NAME: MOCKED_CONF_NAME,
    CONF_PIN: MOCKED_CONF_PIN,
}


@pytest.fixture(autouse=True)
def patch_api():
    with patch(
        "homeassistant.components.bluetooth.async_setup",
        return_value=True,
    ):
        yield


@pytest.fixture
def mock_discovery():
    mock_instance: BluetoothServiceInfoBleak = create_autospec(
        BluetoothServiceInfoBleak, instance=True
    )
    mock_instance.address = MOCKED_CONF_MAC
    mock_instance.name = MOCKED_CONF_NAME
    with patch(
        "homeassistant.components.bluetooth.BluetoothServiceInfoBleak",
        return_value=mock_instance,
    ):
        yield mock_instance


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_success(mock_api: AsyncMock, hass: HomeAssistant):
    """Test entity is created with input data if test_connection is successful."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(return_value=True)
    mock_api.return_value = m_api

    # with empty user data a form is shown
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert "type" in flow_result and flow_result["type"] is FlowResultType.FORM

    # with valid user data the entry is created
    configure_result = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    # Ensure API.test_connection was called
    m_api.test_connection.assert_called()

    # validate input data correctly used
    assert (
        "type" in configure_result
        and configure_result["type"] is FlowResultType.CREATE_ENTRY
    )
    assert "title" in configure_result and configure_result["title"] == MOCKED_CONF_NAME
    assert (
        "data" in configure_result
        and configure_result["data"][CONF_MAC] == MOCKED_CONF_MAC
    )


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_invalid_mac(mock_api: AsyncMock, hass: HomeAssistant) -> None:
    """Test flow rejects invalid MAC address."""
    m_api: API = AsyncMock()
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        {**MOCKED_CONFIG, CONF_MAC: "INVALID-MAC"},
    )

    assert configure_result["type"] is FlowResultType.FORM
    assert configure_result["errors"][CONF_ERROR] == "invalid_mac_code"
    m_api.test_connection.assert_not_called()


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_authentication_error(
    mock_api: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow with authentication error and no resulting cooldown."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(side_effect=APIAuthenticationError(cooldown=0))
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == "error_invalid_authentication"


@pytest.mark.parametrize(
    "cooldown,expected_error",
    [
        (30, "error_auth_cooldown"),
        (0, "error_invalid_authentication"),
        (-5, "error_invalid_authentication"),
    ],
)
@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_authentication_cooldown(
    mock_api: AsyncMock, hass: HomeAssistant, cooldown: int, expected_error: str
) -> None:
    """Test full config flow with authentication cooldown variations."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(
        side_effect=APIAuthenticationError(cooldown=cooldown)
    )
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == expected_error
    if cooldown > 0:
        assert "retry_at" in configure_result["description_placeholders"]
    else:
        assert configure_result.get("description_placeholders") is None


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_device_not_found(
    mock_api: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow when device is not found."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(
        side_effect=APIConnectionDeviceNotFoundError("not found")
    )
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == "error_device_not_found"


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_connection_error(
    mock_api: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow when connection cannot be made."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(side_effect=APIConnectionError("cannot connect"))
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == "error_cannot_connect"


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_user_flow_unknown_error(
    mock_api: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow when unknown error occurs."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(side_effect=Exception("boom"))
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == "error_unknown"


# -------------------------------
# BLUETOOTH FLOW TESTS
# -------------------------------


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_bluetooth_flow_creates_entry(
    mock_api: AsyncMock, hass: HomeAssistant, mock_discovery: Dict[str, Any]
) -> None:
    """Test Bluetooth discovery creates a form."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(return_value=True)
    mock_api.return_value = m_api

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )
    assert flow_result["type"] is FlowResultType.FORM


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_bluetooth_id_already_exists(
    mock_api: AsyncMock, hass: HomeAssistant, mock_discovery: Dict[str, Any]
) -> None:
    """Test Bluetooth discovery aborts if entry already exists."""
    m_api: API = AsyncMock()
    mock_api.return_value = m_api
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )

    assert flow_result["type"] is FlowResultType.ABORT
    assert flow_result["reason"] == "already_configured"
    m_api.test_connection.assert_not_called()


# -------------------------------
# REAUTH FLOW
# -------------------------------


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_reauth_flow(mock_api: AsyncMock, hass: HomeAssistant) -> None:
    """Test reauth flow aborts correctly."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(return_value=True)
    mock_api.return_value = m_api

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
        data={CONF_MAC: MOCKED_CONF_MAC},
    )

    assert flow_result["type"] is FlowResultType.ABORT


@pytest.mark.asyncio
async def test_reauth_entry_does_not_exist(hass: HomeAssistant) -> None:
    """Test reauth fails for non-existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    with pytest.raises(UnknownEntry):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": "non-existing"},
            data=MOCKED_CONFIG,
        )


# -------------------------------
# RECONFIGURE FLOW
# -------------------------------


@patch("custom_components.vogels_motion_mount_ble.config_flow.API")
async def test_reconfigure_flow(mock_api: AsyncMock, hass: HomeAssistant) -> None:
    """Test reconfigure flow aborts correctly."""
    m_api: API = AsyncMock()
    m_api.test_connection = AsyncMock(return_value=True)
    mock_api.return_value = m_api

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        data=MOCKED_CONFIG,
    )

    assert flow_result["type"] is FlowResultType.ABORT


@pytest.mark.asyncio
async def test_reconfigure_entry_does_not_exist(hass: HomeAssistant) -> None:
    """Test reconfigure fails for non-existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    with pytest.raises(UnknownEntry):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": "non-existing"},
            data=MOCKED_CONFIG,
        )


# -------------------------------
# PREFILLED FORM TESTS
# -------------------------------


async def test_prefilled_discovery_form(
    hass: HomeAssistant, mock_discovery: Dict[str, Any]
) -> None:
    """Test prefilled form when discovery info is present."""
    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )

    schema: vol.Schema = flow_result["data_schema"]
    mac_field = schema.schema[CONF_MAC]
    name_field = schema.schema[CONF_NAME]
    pin_field = schema.schema[CONF_PIN]

    assert isinstance(mac_field, TextSelector)
    assert isinstance(name_field, TextSelector)
    assert hasattr(pin_field, "validators") or isinstance(pin_field, NumberSelector)

    assert mac_field.config["read_only"] is True
    assert name_field.config["read_only"] is False
    assert pin_field.validators[0].config["read_only"] is False

    validated: Dict[str, Any] = schema({})
    assert validated[CONF_MAC] == MOCKED_CONF_MAC
    assert validated[CONF_NAME] == MOCKED_CONF_NAME


@pytest.mark.asyncio
async def test_prefilled_reauth_flow_form(hass: HomeAssistant) -> None:
    """Test prefilled reauth flow form (only PIN editable)."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    )

    schema: vol.Schema = flow_result["data_schema"]
    mac_field = schema.schema[CONF_MAC]
    name_field = schema.schema[CONF_NAME]
    pin_field = schema.schema[CONF_PIN]

    assert isinstance(mac_field, TextSelector)
    assert isinstance(name_field, TextSelector)
    assert hasattr(pin_field, "validators") or isinstance(pin_field, NumberSelector)

    assert mac_field.config["read_only"] is True
    assert name_field.config["read_only"] is True
    assert pin_field.validators[0].config["read_only"] is False


@pytest.mark.asyncio
async def test_prefilled_reconfigure_flow_form(hass: HomeAssistant) -> None:
    """Test prefilled reconfigure flow form (MAC read-only, Name editable)."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )

    schema: vol.Schema = flow_result["data_schema"]
    mac_field = schema.schema[CONF_MAC]
    name_field = schema.schema[CONF_NAME]
    pin_field = schema.schema[CONF_PIN]

    assert isinstance(mac_field, TextSelector)
    assert isinstance(name_field, TextSelector)
    assert hasattr(pin_field, "validators") or isinstance(pin_field, NumberSelector)

    assert mac_field.config["read_only"] is True
    assert name_field.config["read_only"] is False
    assert pin_field.validators[0].config["read_only"] is False

    validated: Dict[str, Any] = schema({})
    assert validated[CONF_MAC] == MOCKED_CONF_MAC
    assert validated[CONF_NAME] == MOCKED_CONF_NAME
    assert validated[CONF_PIN] == MOCKED_CONF_PIN
