"""Diagnostics support for Vogels Motion Mount BLE."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_PIN, CONF_MAC
from .coordinator import VogelsMotionMountBleCoordinator
from . import VogelsMotionMountBleConfigEntry

TO_REDACT = {CONF_PIN, CONF_MAC}


async def async_get_config_entry_diagnostics(
    _: HomeAssistant, config_entry: VogelsMotionMountBleConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data

    return {
        "config_entry_data": async_redact_data(dict(config_entry.data), TO_REDACT),
        "vogels_motion_mount_ble_data": coordinator.data,
    }
