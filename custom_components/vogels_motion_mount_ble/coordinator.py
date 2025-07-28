"""Coordinator for Vogels Motion Mount BLE integration in order to hold api."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import API, VogelsMotionMountData
from .const import CONF_MAINTAIN_CONNECTION

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBleCoordinator(DataUpdateCoordinator):
    """Vogels Motion Mount BLE coordinator."""

    data: VogelsMotionMountData

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        # Set variables from values entered in config flow setup
        self.mac = config_entry.data[CONF_HOST]
        self._maintain_connection = config_entry.data[CONF_MAINTAIN_CONNECTION]
        self._name = config_entry.data[CONF_NAME]
        self._pin = config_entry.data.get(CONF_PIN)
        self._loaded = False

        # Initialise DataUpdateCoordinator (that's the device name shown to the user)
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.title,
            config_entry=config_entry,
        )

        # Initialise your api here
        self.api = API(
            mac=self.mac, pin=self._pin, callback=self.async_set_updated_data
        )

        if self._maintain_connection:
            # If maintain_connection is set, start the connection task
            _LOGGER.debug("Starting maintain connection task")
            self.hass.loop.create_task(self.api.maintain_connection())
        else:
            # TODO load initial data
            _LOGGER.debug("Starting maintain connection off")
            self.hass.loop.create_task(self.api.load_initial_data())
