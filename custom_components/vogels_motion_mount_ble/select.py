"""Select entities to define properties for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import DOMAIN, HA_SERVICE_AUTOMOVE_ID, HA_SERVICE_SELECT_AUTOMOVE
from .coordinator import VogelsMotionMountBleCoordinator
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _set_automove_service(call: ServiceCall) -> None:
    _LOGGER.debug("_set_automove_service called with data: %s", call.data)
    await get_coordinator(call).api.set_automove(call.data[HA_SERVICE_AUTOMOVE_ID])

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Selectors for automove."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator
    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SELECT_AUTOMOVE,
        _set_automove_service,
    )
    async_add_entities([AutomoveSelect(coordinator)])


class AutomoveSelect(VogelsMotionMountBleBaseEntity, SelectEntity):
    """Implementation of the Automove Selector."""

    _attr_unique_id = "auto_move"
    _attr_translation_key = _attr_unique_id
    _attr_options = ["off", "hdmi_1", "hdmi_2", "hdmi_3", "hdmi_4", "hdmi_5"]

    @property
    def current_option(self):
        """Return the current active automove option."""
        if self.coordinator.data is None or self.coordinator.data.automove_id is None:
            return None
        if self.coordinator.data.automove_on:
            return self._attr_options[self.coordinator.data.automove_id + 1]
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        index = self._attr_options.index(option)
        # Set index -1 of option or None for "Off"
        await self.coordinator.api.set_automove(index - 1 if (index != 0) else None)
