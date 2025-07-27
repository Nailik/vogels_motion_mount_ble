"""Coordinator for Vogels Motion Mount BLE integration in order to hold api."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import API, VogelsMotionMountData

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBleCoordinator(DataUpdateCoordinator):
    """Vogels Motion Mount BLE coordinator."""

    data: VogelsMotionMountData

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        # Set variables from values entered in config flow setup
        self.mac = config_entry.data[CONF_HOST]
        self._name = config_entry.data[CONF_NAME]
        self._pin = config_entry.data.get(CONF_PIN)

        # Initialise DataUpdateCoordinator (that's the device name shown to the user)
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.title,
            config_entry=config_entry,
        )

        # Initialise your api here
        self.api = API(mac=self.mac, pin=self._pin, coordinator=self)
        hass.loop.create_task(self.api.maintainConnection())
