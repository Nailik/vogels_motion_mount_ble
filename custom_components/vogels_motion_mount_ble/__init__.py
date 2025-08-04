"""Integration for a Vogels Motion Mount via BLE."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)

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
    # Initialise the coordinator that manages data updates from your api.
    coordinator = VogelsMotionMountBleCoordinator(hass, config_entry)
    # Creates initial dictionary for the DOMAIN in hass.data
    hass.data.setdefault(DOMAIN, {})
    # Store coordinator
    hass.data[DOMAIN][config_entry.entry_id] = coordinator
    config_entry.runtime_data = RuntimeData(coordinator)

    config_entry.add_update_listener(update_listener)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Delete device if selected from UI."""
    # TODO: Implement your logic to remove the device.
    return True


async def update_listener(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Update a config entry."""
    # Called when config is changed via the UI
    # Reload the config entry to apply changes
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Unload a config entry."""
    # TODO: Implement your logic to remove the device.
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
