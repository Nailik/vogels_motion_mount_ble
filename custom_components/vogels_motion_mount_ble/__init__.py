"""Integration for a Vogels Motion Mount via BLE."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .services import async_setup_services
from .coordinator import VogelsMotionMountBleCoordinator

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

type VogelsMotionMountBleConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Holds coordinator for access in hass domain."""

    coordinator: DataUpdateCoordinator


async def async_setup(
    hass: HomeAssistant, config: VogelsMotionMountBleConfigEntry
) -> bool:
    """Set up my integration services."""
    _LOGGER.debug("async_setup called with config_entry: %s", config)
    async_setup_services(hass, config)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> bool:
    """Set up VogelsMotionMount Integration from a config entry."""
    _LOGGER.debug("async_setup_entry called with config_entry: %s", config_entry)

    # Registers update listener to update config entry when options are updated.
    unsub_update_listener = config_entry.add_update_listener(async_reload_entry)

    # Initialise the coordinator that manages data updates from your api.
    coordinator = VogelsMotionMountBleCoordinator(
        hass, config_entry, unsub_update_listener
    )

    # Creates initial dictionary for the DOMAIN in hass.data
    hass.data.setdefault(DOMAIN, {})
    # Store coordinator
    hass.data[DOMAIN][config_entry.entry_id] = coordinator
    config_entry.runtime_data = RuntimeData(coordinator)

    # Create entries
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_reload_entry(
    hass: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> None:
    """Reload config entry."""
    _LOGGER.debug("async_reload_entry async_reload")
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
