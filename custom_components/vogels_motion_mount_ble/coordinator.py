"""Coordinator for Vogels Motion Mount BLE integration in order to hold api."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Callable, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import API, VogelsMotionMountData
from .const import CONF_MAC, CONF_NAME, CONF_PIN

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountBleCoordinator(DataUpdateCoordinator):
    """Vogels Motion Mount BLE coordinator."""

    data: VogelsMotionMountData = VogelsMotionMountData()
    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        unsub_options_update_listener: Callable[[], None],
    ) -> None:
        """Initialize coordinator."""
        _LOGGER.debug("Startup coordinator with %s", config_entry.data)
        # Set variables from values entered in config flow setup
        self._unsub_options_update_listener = unsub_options_update_listener
        self.config_entry = config_entry
        self.mac = config_entry.data[CONF_MAC]
        self._name = config_entry.data[CONF_NAME]
        self._pin = config_entry.data.get(CONF_PIN)
        self._loaded = False
        self._hass = hass

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
            pin=self._pin,
            callback=self.async_set_updated_data,
        )

    async def unload(self):
        """Disconnect and unload."""
        _LOGGER.debug("unload coordinator")
        self._unsub_options_update_listener()
        await self.api.unload()
