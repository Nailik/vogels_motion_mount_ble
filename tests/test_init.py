"""Tests the initialization of the Vogels Motion Mount (BLE) integration."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from custom_components.vogels_motion_mount_ble import (
    PLATFORMS,
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.vogels_motion_mount_ble.const import BLE_CALLBACK, DOMAIN
from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountAuthenticationType,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
    IntegrationError,
)

from .conftest import MIN_HA_VERSION, MOCKED_CONF_MAC  # noqa: TID251

# -------------------------------
# region Async setup
# -------------------------------


@pytest.mark.asyncio
async def test_async_setup_version_too_old(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Test that async_setup raises RuntimeError if HA version is too old."""
    with (
        patch("custom_components.vogels_motion_mount_ble.ha_version", "2025.5.0"),
        pytest.raises(IntegrationError),
    ):
        await async_setup(hass, mock_config_entry)


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_bluetooth")
async def test_async_setup_version_ok(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Test that async_setup succeeds if HA version is sufficient."""
    with (
        patch("custom_components.vogels_motion_mount_ble.ha_version", MIN_HA_VERSION),
        patch(
            "custom_components.vogels_motion_mount_ble.async_setup_services", new=Mock()
        ) as mock_services,
    ):
        result = await async_setup(hass, mock_config_entry)
        mock_services.assert_called_once_with(hass)
        assert result is True


@pytest.mark.asyncio
@patch("custom_components.vogels_motion_mount_ble.async_setup_services")
async def test_async_setup(
    mock_async_setup_services: MagicMock,
    mock_config_entry: MagicMock,
    hass: HomeAssistant,
):
    """Setup Integration."""
    # Mock HomeAssistant and config entry
    config_entry = mock_config_entry
    result = await async_setup(hass, config_entry)
    # Assert async_setup_services was called with hass
    mock_async_setup_services.assert_called_once()
    # Assert function returns True
    assert result is True


# -------------------------------
# region Async setup entry
# -------------------------------


@pytest.mark.asyncio
async def test_async_setup_entry_success(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Successful setup scenario."""
    # Mock BLE device, coordinator, and permissions
    mock_config_entry.runtime_data.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Control
    )
    mock_config_entry.runtime_data.data.permissions.auth_status.cooldown = 0

    with patch.object(
        hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
    ) as mock_forward:
        result = await async_setup_entry(hass, mock_config_entry)
        # Assert BLE device found
        # Coordinator first refresh called
        mock_config_entry.runtime_data.async_config_entry_first_refresh.assert_awaited_once()
        # async_forward_entry_setups called
        mock_forward.assert_awaited_once_with(mock_config_entry, PLATFORMS)
        # Setup returned True
        assert result is True


@pytest.mark.asyncio
async def test_async_setup_entry_device_not_found(
    mock_config_entry: MagicMock, mock_dev: AsyncMock, hass: HomeAssistant
):
    """Device discovery fails."""
    mock_dev.return_value = None

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, mock_config_entry)
    # ble callback was created
    assert hass.data[DOMAIN][mock_config_entry.entry_id].get(BLE_CALLBACK)


@pytest.mark.asyncio
async def test_async_setup_entry_refresh_failure(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Coordinator refresh raises exception."""
    mock_config_entry.runtime_data.async_config_entry_first_refresh.side_effect = (
        Exception("refresh failed")
    )
    mock_config_entry.runtime_data.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Control
    )
    mock_config_entry.runtime_data.data.permissions.auth_status.cooldown = 0

    with pytest.raises(ConfigEntryError, match="refresh failed"):
        await async_setup_entry(hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_wrong_permissions_no_cooldown(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Permissions wrong without cooldown."""
    mock_config_entry.runtime_data.async_config_entry_first_refresh.return_value = None
    mock_config_entry.runtime_data.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Wrong
    )
    mock_config_entry.runtime_data.data.permissions.auth_status.cooldown = 0

    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, mock_config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_wrong_permissions_with_cooldown(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Permissions wrong with cooldown."""
    mock_config_entry.runtime_data.async_config_entry_first_refresh.return_value = None
    mock_config_entry.runtime_data.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Wrong
    )
    mock_config_entry.runtime_data.data.permissions.auth_status.cooldown = 120

    with pytest.raises(ConfigEntryAuthFailed) as exc_info:  # noqa: PT012
        await async_setup_entry(hass, mock_config_entry)

        # Ensure the exception contains retry_at
        assert "retry_at" in str(exc_info.value)


@pytest.mark.asyncio
async def test_setup_entry_propagates_homeassistant_error(
    mock_config_entry: MagicMock, hass: HomeAssistant
):
    """Test that HomeAssistantError is propagated and not wrapped as ConfigEntryError."""

    # Patch coordinator to raise ConfigEntryAuthFailed on first refresh
    mock_config_entry.runtime_data.async_config_entry_first_refresh.side_effect = (
        ConfigEntryAuthFailed("auth failed")
    )

    # Test: Should raise ConfigEntryAuthFailed, not ConfigEntryError
    with pytest.raises(ConfigEntryAuthFailed, match="auth failed"):
        await async_setup_entry(hass, mock_config_entry)


# -------------------------------
# region Reload
# -------------------------------


@pytest.mark.asyncio
async def test_async_reload_entry(mock_config_entry: MagicMock):
    """Reloading entry."""
    # Mock HomeAssistant and config_entry
    hass = MagicMock(spec=HomeAssistant)
    async_unload = AsyncMock()
    async_setup_entry = AsyncMock()

    # Patch async_unload_entry and async_setup_entry to track calls
    with (
        patch(
            "custom_components.vogels_motion_mount_ble.async_unload_entry", async_unload
        ),
        patch(
            "custom_components.vogels_motion_mount_ble.async_setup_entry",
            async_setup_entry,
        ),
    ):
        await async_reload_entry(hass, mock_config_entry)

        # Assert reloading was called with correct entry_id
        async_unload.assert_awaited_once_with(hass, mock_config_entry)
        async_setup_entry.assert_awaited_once_with(hass, mock_config_entry)


# -------------------------------
# region Unload
# -------------------------------


@pytest.mark.asyncio
@patch(
    "custom_components.vogels_motion_mount_ble.__init__.bluetooth.async_rediscover_address"
)
async def test_async_unload_entry_success(
    mock_rediscover: AsyncMock, mock_config_entry: MagicMock
):
    """async_unload_platforms returns true: platforms unloaded, coordinator unload + rediscover called."""

    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        mock_config_entry, PLATFORMS
    )
    mock_config_entry.runtime_data.unload.assert_awaited_once()
    mock_rediscover.assert_called_once_with(hass, MOCKED_CONF_MAC)


@pytest.mark.asyncio
@patch(
    "custom_components.vogels_motion_mount_ble.__init__.bluetooth.async_rediscover_address"
)
async def test_async_unload_entry_failure(
    mock_rediscover: AsyncMock, mock_config_entry: MagicMock
):
    """async_unload_platforms returns false: platforms not unloaded, coordinator unload + rediscover not called."""

    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

    coordinator = MagicMock()
    coordinator.unload = AsyncMock()

    result = await async_unload_entry(hass, mock_config_entry)

    assert result is False
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        mock_config_entry, PLATFORMS
    )
    coordinator.unload.assert_not_awaited()
    mock_rediscover.assert_not_called()
