"""Integration for a Vogels Motion Mount via BLE."""

from __future__ import annotations

import logging
from homeassistant.const import __version__ as ha_version
from packaging import version
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
)

from .api import APIAuthenticationError, APIConnectionDeviceNotFoundError
from .coordinator import VogelsMotionMountBleCoordinator
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

# for this version read_only was added to config selectors
MIN_HA_VERSION = "2025.6.0"

if version.parse(ha_version) < version.parse(MIN_HA_VERSION):
    raise RuntimeError(
        f"Vogels Motion Mount BLE requires Home Assistant {MIN_HA_VERSION}+"
    )


async def async_setup(
    hass: HomeAssistant, entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Set up Vogels Motion Mount integration services."""
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
    coordinator = VogelsMotionMountBleCoordinator(
        hass=hass,
        config_entry=config_entry,
        unsub_update_listener=unsub_update_listener,
    )

    try:
        await coordinator.api.refresh_data()
    except APIConnectionDeviceNotFoundError as err:
        raise ConfigEntryNotReady("error_device_not_found") from err
    except APIAuthenticationError as err:
        raise ConfigEntryAuthFailed("error_invalid_athentication") from err
    except Exception as err:
        raise ConfigEntryError(
            translation_key=f"Something went wrong {err}",
            translation_placeholders={"error": err},
        ) from err

    config_entry.runtime_data = coordinator
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

    return unload_ok
