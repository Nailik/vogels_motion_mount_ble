"""Integration for a Vogels Motion Mount via BLE."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_OPTIONS_UPDATE_LISTENER
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)
from homeassistant.const import Platform

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.TEXT,
]

type VogelsMotionMountBleConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Holds coordinator for access in hass domain."""

    coordinator: DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Set up VogelsMotionMount Integration from a config entry."""
    _LOGGER.debug("async_setup_entry called with config_entry: %s", config_entry)

    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = config_entry.add_update_listener(update_listener)

    # Initialise the coordinator that manages data updates from your api.
    coordinator = VogelsMotionMountBleCoordinator(
        hass, config_entry, unsub_options_update_listener
    )
    # Creates initial dictionary for the DOMAIN in hass.data
    hass.data.setdefault(DOMAIN, {})
    # Store coordinator
    hass.data[DOMAIN][config_entry.entry_id] = coordinator
    config_entry.runtime_data = RuntimeData(coordinator)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Delete device if selected from UI."""
    _LOGGER.debug("async_remove_config_entry_device")
    # TODO: Implement your logic to remove the device.
    # bluetooth.async_rediscover_address(hass, "44:44:33:11:23:42")
    return True


async def update_listener(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Update a config entry."""
    # Called when config is changed via the UI
    # Reload the config entry to apply changes
    _LOGGER.debug("update_listener async_reload")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.debug("options_update_listener async_reload")
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
        # Remove config entry from domain.
        coordinator: VogelsMotionMountBleCoordinator = hass.data[DOMAIN].pop(
            config_entry.entry_id
        )
        # Disconnect and remove options_update_listener.
        await coordinator.unload()

    return unload_ok
