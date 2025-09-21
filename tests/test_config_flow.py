import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from typing import Any, Dict
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
from bleak import BLEDevice
from unittest.mock import create_autospec

from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountAuthenticationType,
    VogelsMotionMountPermissions,
    VogelsMotionMountAuthenticationStatus,
)

MOCKED_CONF_MAC = "AA:BB:CC:DD:EE:FF"
MOCKED_CONF_NAME = "Mount"
MOCKED_CONF_PIN = 1234

MOCKED_CONFIG: Dict[str, Any] = {
    CONF_MAC: MOCKED_CONF_MAC,
    CONF_NAME: MOCKED_CONF_NAME,
    CONF_PIN: MOCKED_CONF_PIN,
}


@pytest.fixture(autouse=True)
def mock_integration():
    with patch(
        "bleak_retry_connector.establish_connection", new_callable=AsyncMock
    ) as mock_conn, patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        return_value=BLEDevice(
            address=MOCKED_CONF_MAC, name=MOCKED_CONF_NAME, details={}
        ),
    ) as mock_dev, patch(
        "custom_components.vogels_motion_mount_ble.__init__.VogelsMotionMountBleCoordinator",
        return_value=MagicMock(),
    ) as mock_coord:
        mock_conn.return_value = AsyncMock()
        yield mock_coord, mock_conn, mock_dev


@pytest.fixture(autouse=True)
def patch_api():
    with patch(
        "homeassistant.components.bluetooth.async_setup", return_value=True
    ), patch(
        "custom_components.vogels_motion_mount_ble.async_setup", return_value=True
    ), patch(
        "custom_components.vogels_motion_mount_ble.async_setup_entry", return_value=True
    ):
        yield


def make_permissions(
    auth_type: VogelsMotionMountAuthenticationType, cooldown: int | None = None
):
    """Return a factory to make permissions with customizable auth_status."""
    return VogelsMotionMountPermissions(
        auth_status=VogelsMotionMountAuthenticationStatus(
            auth_type=auth_type,
            cooldown=cooldown,
        ),
        change_settings=True,
        change_default_position=True,
        change_name=True,
        change_presets=True,
        change_tv_on_off_detection=True,
        disable_channel=True,
        start_calibration=True,
    )


@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_user_flow_success(mock_get_permissions: AsyncMock, hass: HomeAssistant):
    """Test entity is created with input data if test_connection is successful."""
    mock_get_permissions.return_value = make_permissions(
        auth_type=VogelsMotionMountAuthenticationType.Full,
    )
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

    mock_get_permissions.assert_awaited_once()

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


@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_user_flow_invalid_mac(
    mock_get_permissions: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow rejects invalid MAC address."""
    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        {**MOCKED_CONFIG, CONF_MAC: "INVALID-MAC"},
    )

    assert configure_result["type"] is FlowResultType.FORM
    assert configure_result["errors"][CONF_ERROR] == "invalid_mac_code"
    mock_get_permissions.assert_not_called()


@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_user_flow_authentication_error(
    mock_get_permissions: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow with authentication error and no resulting cooldown."""
    mock_get_permissions.return_value = make_permissions(
        auth_type=VogelsMotionMountAuthenticationType.Wrong,
    )

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    mock_get_permissions.assert_awaited_once()

    assert configure_result["errors"][CONF_ERROR] == "error_invalid_authentication"


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


@pytest.mark.parametrize(
    "cooldown,expected_error",
    [
        (30, "error_invalid_authentication_cooldown"),
        (0, "error_invalid_authentication"),
        (-5, "error_invalid_authentication"),
    ],
)
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_user_flow_authentication_cooldown(
    mock_get_permissions: AsyncMock,
    hass: HomeAssistant,
    cooldown: int,
    expected_error: str,
) -> None:
    """Test full config flow with authentication cooldown variations."""
    mock_get_permissions.return_value = make_permissions(
        auth_type=VogelsMotionMountAuthenticationType.Wrong,
        cooldown=cooldown,
    )

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    mock_get_permissions.assert_awaited_once()

    assert configure_result["errors"][CONF_ERROR] == expected_error
    if cooldown > 0:
        assert "retry_at" in configure_result["description_placeholders"]
    else:
        assert configure_result.get("description_placeholders") is None


@pytest.mark.asyncio
@patch(
    "homeassistant.components.bluetooth.async_ble_device_from_address",
    return_value=None,
)
async def test_user_flow_device_not_found(
    mock_device: AsyncMock, hass: HomeAssistant
) -> None:
    mock_device = AsyncMock()
    mock_device.return_value = None

    """Test flow when device is not found."""
    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == "error_device_not_found"


@pytest.mark.asyncio
@patch(
    "homeassistant.components.bluetooth.async_ble_device_from_address",
    return_value=AsyncMock,
)
async def test_user_flow_connection_error(
    mock_device: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow when connection cannot be made."""
    mock_device = AsyncMock()
    mock_device.side_effect = Exception("Device error")

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    configure_result: Dict[str, Any] = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"],
        MOCKED_CONFIG,
    )

    assert configure_result["errors"][CONF_ERROR] == "error_unknown"


@pytest.mark.asyncio
async def test_user_flow_unknown_error(
    mock_integration: AsyncMock, hass: HomeAssistant
) -> None:
    """Test flow when unknown error occurs."""
    _, mock_conn, _ = mock_integration
    mock_conn.side_effect = Exception("Connection failed")
    with pytest.raises(Exception):
        await mock_conn()

        flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        configure_result: Dict[
            str, Any
        ] = await hass.config_entries.flow.async_configure(
            flow_result["flow_id"],
            MOCKED_CONFIG,
        )

        assert configure_result["errors"][CONF_ERROR] == "error_unknown"


# -------------------------------
# BLUETOOTH FLOW TESTS
# -------------------------------


@pytest.mark.asyncio
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_bluetooth_flow_creates_entry(
    mock_get_permissions: AsyncMock, hass: HomeAssistant, mock_discovery: Dict[str, Any]
) -> None:
    """Test Bluetooth discovery creates a form."""
    mock_get_permissions.return_value = make_permissions(
        auth_type=VogelsMotionMountAuthenticationType.Full,
    )

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )
    assert flow_result["type"] is FlowResultType.FORM


@pytest.mark.asyncio
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_bluetooth_id_already_exists(
    mock_get_permissions: AsyncMock, hass: HomeAssistant, mock_discovery: Dict[str, Any]
) -> None:
    """Test Bluetooth discovery aborts if entry already exists."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCKED_CONF_MAC, data=MOCKED_CONFIG
    )
    entry.add_to_hass(hass)

    flow_result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )

    assert flow_result["type"] is FlowResultType.ABORT
    assert flow_result["reason"] == "already_configured"
    mock_get_permissions.assert_not_called()


# -------------------------------
# REAUTH FLOW
# -------------------------------


@pytest.mark.asyncio
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_reauth_flow(
    mock_get_permissions: AsyncMock, hass: HomeAssistant
) -> None:
    """Test reauth flow aborts correctly."""
    mock_get_permissions.return_value = make_permissions(
        auth_type=VogelsMotionMountAuthenticationType.Full,
    )

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
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_reauth_entry_does_not_exist(
    mock_get_permissions: AsyncMock, hass: HomeAssistant
) -> None:
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
    mock_get_permissions.assert_not_called


# -------------------------------
# RECONFIGURE FLOW
# -------------------------------


@pytest.mark.asyncio
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_reconfigure_flow(
    mock_get_permissions: AsyncMock, hass: HomeAssistant
) -> None:
    """Test reconfigure flow aborts correctly."""
    mock_get_permissions.return_value = make_permissions(
        auth_type=VogelsMotionMountAuthenticationType.Full,
    )

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
@patch("custom_components.vogels_motion_mount_ble.config_flow.get_permissions")
async def test_reconfigure_entry_does_not_exist(
    mock_get_permissions: AsyncMock, hass: HomeAssistant
) -> None:
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
    mock_get_permissions.assert_not_called


# -------------------------------
# PREFILLED FORM TESTS
# -------------------------------


@pytest.mark.asyncio
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
