"""Integration for a Vogels Motion Mount via BLE."""

from __future__ import annotations

from datetime import timedelta
import logging

from packaging import version

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, __version__ as ha_version
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
    IntegrationError,
)
from homeassistant.util import dt as dt_util

from .const import CONF_MAC, MIN_HA_VERSION
from .coordinator import VogelsMotionMountBleCoordinator
from .data import VogelsMotionMountAuthenticationType
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

type VogelsMotionMountBleConfigEntry = ConfigEntry[VogelsMotionMountBleCoordinator]


async def async_setup(
    hass: HomeAssistant, entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Set up Vogels Motion Mount integration services."""
    if version.parse(ha_version) < version.parse(MIN_HA_VERSION):
        raise IntegrationError(
            translation_key="invalid_ha_version",
            translation_placeholders={"version": MIN_HA_VERSION},
        )
    _LOGGER.debug("async_setup called with config_entry: %s", entry)
    async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Set up Vogels Motion Mount Integration from a config entry."""
    _LOGGER.debug("async_setup_entry called with config_entry: %s", config_entry)

    # Registers update listener to update config entry when options are updated.
    unsub_update_listener = config_entry.add_update_listener(async_reload_entry)

    # Initialise the coordinator that manages data updates from your api.
    device = bluetooth.async_ble_device_from_address(
        hass=hass,
        address=config_entry.data[CONF_MAC],
        connectable=True,
    )

    if device is None:
        raise ConfigEntryNotReady("error_device_not_found")

    coordinator = VogelsMotionMountBleCoordinator(
        hass=hass,
        config_entry=config_entry,
        device=device,
        unsub_options_update_listener=unsub_update_listener,
    )
    config_entry.runtime_data = coordinator

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryError(
            translation_key="error_unknown",
            translation_placeholders={"error": str(err)},
        ) from err

    permissions = coordinator.data.permissions
    if permissions.auth_status.auth_type == VogelsMotionMountAuthenticationType.Wrong:
        if permissions.auth_status.cooldown and permissions.auth_status.cooldown > 0:
            retry_time = dt_util.now() + timedelta(
                seconds=permissions.auth_status.cooldown
            )
            raise ConfigEntryAuthFailed(
                translation_key="error_invalid_authentication_cooldown",
                translation_placeholders={
                    "retry_at": retry_time.strftime("%Y-%m-%d %H:%M:%S")
                },
            )
        raise ConfigEntryAuthFailed("error_invalid_authentication")

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_reload_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> None:
    """Reload config entry."""
    _LOGGER.debug(
        "async_reload_entry async_reload with pin %s", config_entry.data["conf_pin"]
    )
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry")
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        _LOGGER.debug("async_unload_entry pop")
        coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data
        await coordinator.unload()
        bluetooth.async_rediscover_address(hass, config_entry.data[CONF_MAC])

    return unload_ok
