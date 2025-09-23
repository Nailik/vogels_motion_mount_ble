import pytest

from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountAuthenticationType,
)
from custom_components.vogels_motion_mount_ble import (
    async_unload_entry,
    async_setup,
    async_setup_entry,
    async_reload_entry,
    PLATFORMS,
)


from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
    IntegrationError,
)

from unittest.mock import AsyncMock, patch, MagicMock, Mock

from . import (
    MOCKED_CONF_ENTRY_ID,
    MOCKED_CONFIG,
    DOMAIN,
    MIN_HA_VERSION,
    MOCKED_CONF_MAC,
)


def make_config_entry(mock_coord: MagicMock) -> MagicMock:
    config_entry = MagicMock()
    config_entry.entry_id = MOCKED_CONF_ENTRY_ID
    config_entry.data = MOCKED_CONFIG
    config_entry.domain = DOMAIN
    config_entry.runtime_data = mock_coord
    return config_entry


# -------------------------------
# endregion
# region Async setup
# -------------------------------


@pytest.mark.asyncio
async def test_async_setup_version_too_old(mock_coord: MagicMock, hass: HomeAssistant):
    """Test that async_setup raises RuntimeError if HA version is too old."""
    with patch("custom_components.vogels_motion_mount_ble.ha_version", "2025.5.0"):
        with pytest.raises(IntegrationError):
            await async_setup(hass, make_config_entry(mock_coord))


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_bluetooth", "patch_default_bleak_client")
async def test_async_setup_version_ok(mock_coord: MagicMock, hass: HomeAssistant):
    """Test that async_setup succeeds if HA version is sufficient."""
    with patch(
        "custom_components.vogels_motion_mount_ble.ha_version", MIN_HA_VERSION
    ), patch(
        "custom_components.vogels_motion_mount_ble.async_setup_services", new=Mock()
    ) as mock_services:
        result = await async_setup(hass, make_config_entry(mock_coord))
        mock_services.assert_called_once_with(hass)
        assert result is True


@pytest.mark.asyncio
@patch("custom_components.vogels_motion_mount_ble.async_setup_services")
async def test_async_setup(
    mock_async_setup_services: MagicMock, mock_coord: MagicMock, hass: HomeAssistant
):
    # Mock HomeAssistant and config entry
    config_entry = make_config_entry(mock_coord)
    result = await async_setup(hass, config_entry)
    # Assert async_setup_services was called with hass
    mock_async_setup_services.assert_called_once()
    # Assert function returns True
    assert result is True


# -------------------------------
# endregion
# region Async setup entry
# -------------------------------


@pytest.mark.asyncio
async def test_async_setup_entry_success(mock_coord: MagicMock, hass: HomeAssistant):
    """Successful setup scenario."""
    config_entry = make_config_entry(mock_coord)

    # Mock BLE device, coordinator, and permissions
    mock_coord.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Control
    )
    mock_coord.data.permissions.auth_status.cooldown = 0

    with patch.object(
        hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
    ) as mock_forward:
        result = await async_setup_entry(hass, config_entry)
        # Assert BLE device found
        assert config_entry.runtime_data == mock_coord
        # Coordinator first refresh called
        mock_coord.async_config_entry_first_refresh.assert_awaited_once()
        # async_forward_entry_setups called
        mock_forward.assert_awaited_once_with(config_entry, PLATFORMS)
        # Setup returned True
        assert result is True


@pytest.mark.asyncio
async def test_async_setup_entry_device_not_found(
    mock_coord: MagicMock, mock_dev: AsyncMock, hass: HomeAssistant
):
    """Device discovery fails."""
    config_entry = make_config_entry(mock_coord)
    mock_dev.return_value = None

    with pytest.raises(ConfigEntryNotReady, match="error_device_not_found"):
        await async_setup_entry(hass, config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_refresh_failure(
    mock_coord: MagicMock, hass: HomeAssistant
):
    """Coordinator refresh raises exception."""
    config_entry = make_config_entry(mock_coord)
    mock_coord.async_config_entry_first_refresh.side_effect = Exception(
        "refresh failed"
    )
    mock_coord.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Control
    )
    mock_coord.data.permissions.auth_status.cooldown = 0

    with pytest.raises(ConfigEntryError, match="refresh failed"):
        await async_setup_entry(hass, config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_wrong_permissions_no_cooldown(
    mock_coord: MagicMock, hass: HomeAssistant
):
    """Permissions wrong without cooldown."""
    config_entry = make_config_entry(mock_coord)
    mock_coord.async_config_entry_first_refresh.return_value = None
    mock_coord.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Wrong
    )
    mock_coord.data.permissions.auth_status.cooldown = 0

    with pytest.raises(ConfigEntryAuthFailed, match="error_invalid_authentication"):
        await async_setup_entry(hass, config_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_wrong_permissions_with_cooldown(
    mock_coord: MagicMock, hass: HomeAssistant
):
    """Permissions wrong with cooldown."""
    config_entry = make_config_entry(mock_coord)
    mock_coord.async_config_entry_first_refresh.return_value = None
    mock_coord.data.permissions.auth_status.auth_type = (
        VogelsMotionMountAuthenticationType.Wrong
    )
    mock_coord.data.permissions.auth_status.cooldown = 120

    with pytest.raises(ConfigEntryAuthFailed) as exc_info:
        await async_setup_entry(hass, config_entry)

        # Ensure the exception contains retry_at
        assert "retry_at" in str(exc_info.value)


# -------------------------------
# endregion
# region Reload
# -------------------------------


@pytest.mark.asyncio
async def test_async_reload_entry(mock_coord: MagicMock):
    # Mock HomeAssistant and config_entry
    hass = MagicMock(spec=HomeAssistant)
    hass.config_entries.async_reload = AsyncMock()

    await async_reload_entry(hass, make_config_entry(mock_coord))

    # Assert async_reload was called with correct entry_id
    hass.config_entries.async_reload.assert_awaited_once_with(MOCKED_CONF_ENTRY_ID)


# -------------------------------
# endregion
# region Unload
# -------------------------------


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_bluetooth", "patch_default_bleak_client")
async def test_async_unload_entry_success(mock_rediscover: AsyncMock):
    """async_unload_platforms returns true: platforms unloaded, coordinator unload + rediscover called."""

    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    coordinator = MagicMock()
    coordinator.unload = AsyncMock()
    config_entry = make_config_entry(coordinator)

    result = await async_unload_entry(hass, config_entry)

    assert result is True
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        config_entry, PLATFORMS
    )
    coordinator.unload.assert_awaited_once()
    mock_rediscover.assert_called_once_with(hass, MOCKED_CONF_MAC)


@pytest.mark.asyncio
@patch(
    "custom_components.vogels_motion_mount_ble.__init__.bluetooth.async_rediscover_address"
)
async def test_async_unload_entry_failure(mock_rediscover: AsyncMock):
    """async_unload_platforms returns false: platforms not unloaded, coordinator unload + rediscover not called."""

    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

    coordinator = MagicMock()
    coordinator.unload = AsyncMock()
    config_entry = make_config_entry(coordinator)

    result = await async_unload_entry(hass, config_entry)

    assert result is False
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        config_entry, PLATFORMS
    )
    coordinator.unload.assert_not_awaited()
    mock_rediscover.assert_not_called()
