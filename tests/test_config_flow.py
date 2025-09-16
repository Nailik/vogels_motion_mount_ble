import pytest
from unittest.mock import AsyncMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.data_entry_flow import FlowResultType
from custom_components.vogels_motion_mount_ble.api import APIAuthenticationError
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from homeassistant.helpers import selector
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
MOCKED_CONFIG = {
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
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCKED_CONFIG,
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == MOCKED_CONF_NAME
    assert result2["data"][CONF_MAC] == MOCKED_CONF_MAC


async def test_user_flow_invalid_mac(hass, mock_api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCKED_CONFIG, CONF_MAC: "INVALID-MAC"},
    )

    assert result2["type"] is FlowResultType.FORM
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
        MOCKED_CONFIG,
    )

    assert result2["errors"][CONF_ERROR] == "error_invalid_authentication"


async def test_user_flow_authentication_cooldown_positive(hass):
    """Test full config flow with cooldown > 0."""
    with patch(
        "custom_components.vogels_motion_mount_ble.config_flow.API",
        autospec=True,
    ) as mock_api:
        mock_api.return_value.test_connection = AsyncMock(
            side_effect=lambda: Exception("mock")  # placeholder
        )
        # Use side effect to simulate APIAuthenticationError with cooldown
        from custom_components.vogels_motion_mount_ble.api import APIAuthenticationError

        mock_api.return_value.test_connection.side_effect = APIAuthenticationError(
            "auth error", cooldown=30
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCKED_CONFIG,
        )

        assert result2["errors"][CONF_ERROR] == "error_auth_cooldown"
        # In your code, the placeholder key is "retry_at"
        assert "retry_at" in result2["description_placeholders"]


async def test_user_flow_authentication_cooldown_zero(hass):
    """Test full config flow with cooldown == 0."""
    with patch(
        "custom_components.vogels_motion_mount_ble.config_flow.API",
        autospec=True,
    ) as mock_api:
        from custom_components.vogels_motion_mount_ble.api import APIAuthenticationError

        mock_api.return_value.test_connection = AsyncMock(
            side_effect=APIAuthenticationError("auth error", cooldown=0)
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCKED_CONFIG,
        )

        assert result2["errors"][CONF_ERROR] == "error_invalid_authentication"
        assert result2.get("description_placeholders") is None


async def test_user_flow_authentication_cooldown_negative(hass):
    """Test full config flow with cooldown < 0."""
    with patch(
        "custom_components.vogels_motion_mount_ble.config_flow.API",
        autospec=True,
    ) as mock_api:
        from custom_components.vogels_motion_mount_ble.api import APIAuthenticationError

        mock_api.return_value.test_connection = AsyncMock(
            side_effect=APIAuthenticationError("auth error", cooldown=-5)
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCKED_CONFIG,
        )

        assert result2["errors"][CONF_ERROR] == "error_invalid_authentication"
        assert result2.get("description_placeholders") is None


async def test_user_flow_device_not_found(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(
        side_effect=APIConnectionDeviceNotFoundError("not found")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCKED_CONFIG,
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
        MOCKED_CONFIG,
    )
    assert result2["errors"][CONF_ERROR] == "error_cannot_connect"


async def test_user_flow_unknown_error(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(side_effect=Exception("boom"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCKED_CONFIG,
    )
    assert result2["errors"][CONF_ERROR] == "error_unknown"


async def test_bluetooth_flow_creates_entry(hass, mock_api, mock_discovery):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )

    assert result["type"] is FlowResultType.FORM


async def test_bluetooth_id_already_exists(hass, mock_api, mock_discovery):
    # Create a mock entry with the same MAC
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    flow = hass.config_entries.flow
    result = await flow.async_init(
        DOMAIN, context={"source": "bluetooth"}, data=mock_discovery
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # Ensure API.test_connection was never called
    mock_api.return_value.test_connection.assert_not_called()


async def test_reauth_flow(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    assert hass.config_entries.async_entries(DOMAIN)[0] == entry

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
        data={CONF_MAC: "AA:BB:CC:DD:EE:FF"},
    )
    assert result["type"] is FlowResultType.ABORT


async def test_reauth_entry_does_not_exist(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCKED_CONF_MAC,
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    assert hass.config_entries.async_entries(DOMAIN)[0] == entry

    with pytest.raises(UnknownEntry):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": "non-existing"},
            data=MOCKED_CONFIG,
        )


async def test_reconfigure_flow(hass, mock_api):
    mock_api.return_value.test_connection = AsyncMock(return_value=True)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCKED_CONF_MAC,
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    assert hass.config_entries.async_entries(DOMAIN)[0] == entry

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        data={CONF_MAC: "AA:BB:CC:DD:EE:FF"},
    )
    assert result["type"] is FlowResultType.ABORT


async def test_reconfigure_entry_does_not_exist(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCKED_CONF_MAC,
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    assert hass.config_entries.async_entries(DOMAIN)[0] == entry

    with pytest.raises(UnknownEntry):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": "non-existing"},
            data=MOCKED_CONFIG,
        )


async def test_prefilled_discovery_form(hass, mock_discovery):
    """Test prefilled form when discovery info is present."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=mock_discovery
    )

    schema: vol.Schema = flow_result["data_schema"]
    mac_field = schema.schema[CONF_MAC]
    name_field = schema.schema[CONF_NAME]

    assert isinstance(mac_field, selector.TextSelector)
    assert isinstance(name_field, selector.TextSelector)

    # Check read_only flags
    assert mac_field.config["read_only"] is True
    assert name_field.config["read_only"] is False

    # Check defaults
    validated = schema({})
    assert validated[CONF_MAC] == MOCKED_CONF_MAC
    assert validated[CONF_NAME] == MOCKED_CONF_NAME


@pytest.mark.asyncio
async def test_prefilled_reauth_flow_form(hass, mock_api):
    """Test prefilled form when doing a reauth flow (only PIN editable)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCKED_CONF_MAC,
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
    )

    schema: vol.Schema = flow_result["data_schema"]
    mac_field = schema.schema[CONF_MAC]
    name_field = schema.schema[CONF_NAME]
    pin_field = schema.schema[CONF_PIN]

    # Types
    assert isinstance(mac_field, selector.TextSelector)
    assert isinstance(name_field, selector.TextSelector)
    assert hasattr(pin_field, "validators") or isinstance(
        pin_field, selector.NumberSelector
    )

    # Read-only flags
    assert mac_field.config["read_only"] is True  # MAC not editable
    assert name_field.config["read_only"] is True  # Name not editable
    assert pin_field.validators[0].config["read_only"] is False  # PIN editable


@pytest.mark.asyncio
async def test_prefilled_reconfigure_flow_form(hass, mock_api):
    """Test prefilled form when doing a reconfigure flow (both MAC and Name editable)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCKED_CONF_MAC,
        data=MOCKED_CONFIG,
    )
    entry.add_to_hass(hass)

    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    print("DEBUG: ", flow_result)
    schema: vol.Schema = flow_result["data_schema"]
    mac_field = schema.schema[CONF_MAC]
    name_field = schema.schema[CONF_NAME]
    pin_field = schema.schema[CONF_PIN]

    # Types
    assert isinstance(mac_field, selector.TextSelector)
    assert isinstance(name_field, selector.TextSelector)
    assert hasattr(pin_field, "validators") or isinstance(
        pin_field, selector.NumberSelector
    )

    # Read-only flags
    assert mac_field.config["read_only"] is True  # MAC editable
    assert name_field.config["read_only"] is False  # Name editable
    assert pin_field.validators[0].config["read_only"] is False  # PIN editable

    # Defaults
    validated = schema({})
    assert validated[CONF_MAC] == MOCKED_CONF_MAC
    assert validated[CONF_NAME] == MOCKED_CONF_NAME
    assert validated[CONF_PIN] == MOCKED_CONF_PIN
