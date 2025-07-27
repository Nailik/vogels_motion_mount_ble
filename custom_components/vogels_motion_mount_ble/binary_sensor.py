"""Interfaces with the Integration 101 Template api sensors."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MyConfigEntry
from .base import ExampleBaseEntity
from .const import DOMAIN
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from homeassistant.helpers.typing import ConfigType
from homeassistant.core import HomeAssistant, ServiceCall, callback

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Binary Sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ExampleBinarySensor(coordinator)])


class ExampleBinarySensor(ExampleBaseEntity, BinarySensorEntity):
    """Implementation of a sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_translation_key = "connection"
    _attr_should_poll = True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        _LOGGER.exception("_handle_coordinator_update binary sensor")
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "connection"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.coordinator.mac}-connected"

    @property
    def is_on(self) -> bool:
        """Return if the binary sensor is on."""
        _LOGGER.exception("is_on binary sensor")
        if not self.coordinator.data:
            _LOGGER.error("No data available in coordinator")
            return None
        # This needs to enumerate to true or false
        return self.coordinator.data.connected

