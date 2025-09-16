"""Utility methods."""

from homeassistant.core import ServiceCall

from .const import HA_SERVICE_DEVICE_ID
from .coordinator import VogelsMotionMountBleCoordinator


def get_coordinator(call: ServiceCall) -> VogelsMotionMountBleCoordinator:
    """Extract device_ids from service call and return list of coordinators."""
    entry_id = call.data.get(HA_SERVICE_DEVICE_ID)
    return call.hass.config_entries.async_get_entry(entry_id).runtime_data
