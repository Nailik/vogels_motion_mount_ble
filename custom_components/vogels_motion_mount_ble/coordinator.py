"""Coordinator for Vogels Motion Mount BLE integration in order to hold api."""

import logging

from homeassistant.components import bluetooth
from homeassistant.core import Callable, HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import API, VogelsMotionMountData
from .const import CONF_PIN, CONF_MAC, CONF_NAME

_LOGGER = logging.getLogger(__name__)
from homeassistant.const import Platform

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.TEXT,
]


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
        _LOGGER.debug("startup coordingtor with %s", config_entry.data)
        # Set variables from values entered in config flow setup
        self._unsub_options_update_listener = unsub_options_update_listener
        self.config_entry = config_entry
        self.mac = config_entry.data[CONF_MAC]
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
            hass=hass,
            mac=self.mac,
            pin=self._pin,
            callback=self.async_set_updated_data,  # todo setup presets - only if changed? add/remove the entities to have the correct names?
        )

        self._setup_task = hass.loop.create_task(self._setup())

    async def _setup(self):
        _LOGGER.error("_setup called")
        # todo if this throws an error (e.g. due to invalid pin) this should show an error in the ui
        await self.api.load_initial_data()
        await self.hass.config_entries.async_forward_entry_setups(
            self.config_entry, PLATFORMS
        )

    async def unload(self):
        self._unsub_options_update_listener()
        if self._setup_task:
            self._setup_task.cancel()
        await self.api.disconnect()
