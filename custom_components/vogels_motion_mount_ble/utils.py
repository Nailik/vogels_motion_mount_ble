import logging

from homeassistant.core import ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, HA_SERVICE_DEVICE_ID
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)


def get_coordinator(call: ServiceCall) -> VogelsMotionMountBleCoordinator:
    """Extract device_ids from service call and return list of coordinators."""
    device_registry = dr.async_get(call.hass)
    device = device_registry.async_get(call.data.get(HA_SERVICE_DEVICE_ID))
    entry_id = next(iter(device.config_entries))
    return call.hass.data[DOMAIN][entry_id]
