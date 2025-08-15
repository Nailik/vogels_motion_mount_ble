"""Coordinator for Vogels Motion Mount BLE integration in order to hold api."""

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import API, VogelsMotionMountData
from .const import CONF_CONTROL_PIN, CONF_MAC, CONF_NAME, CONF_SETTINGS_PIN

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBleCoordinator(DataUpdateCoordinator):
    """Vogels Motion Mount BLE coordinator."""

    data: VogelsMotionMountData = VogelsMotionMountData()

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        # Set variables from values entered in config flow setup
        self.mac = config_entry.data[CONF_MAC]
        self._name = config_entry.data[CONF_NAME]
        self._settings_pin = config_entry.data.get(CONF_SETTINGS_PIN)
        self._control_pin = config_entry.data.get(CONF_CONTROL_PIN)
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
            hass=hass,
            mac=self.mac,
            settings_pin=self._settings_pin,
            control_pin=self._control_pin,
            callback=self.async_set_updated_data,
        )

        hass.loop.create_task(self.api.load_initial_data())
