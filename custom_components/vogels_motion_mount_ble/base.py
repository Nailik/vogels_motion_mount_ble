"""Base entity to define common properties and methods for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBleBaseEntity(CoordinatorEntity):
    """Base Entity Class."""

    coordinator: VogelsMotionMountBleCoordinator
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self.coordinator.name,
            manufacturer="Vogels",
            model="Motion Mount",
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()
