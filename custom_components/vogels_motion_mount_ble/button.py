import logging

import voluptuous as vol

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MyConfigEntry
from .base import ExampleBaseEntity
from .const import DOMAIN, HA_SERVICE_SELECT_PRESET, HA_SERVICE_SELECT_PRESET_ID
from .coordinator import ExampleCoordinator
from homeassistant.core import ServiceCall

_LOGGER = logging.getLogger(__name__)

HA_SERVICE_SELECT_PRESET_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(HA_SERVICE_SELECT_PRESET_ID): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=7, mode=selector.NumberSelectorMode.BOX
            )
        ),
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Buttons."""
    coordinator: ExampleCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async def _select_preset_service(call: ServiceCall) -> None:
        """My first service."""
        await coordinator.api.select_preset(call[HA_SERVICE_SELECT_PRESET_ID])

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SELECT_PRESET,
        _select_preset_service,
        schema=HA_SERVICE_SELECT_PRESET_SERVICE_SCHEMA,
    )

    # Add one SelectPresetButton for each preset_id from 0 to 7 inclusive
    async_add_entities(
        [SelectPresetButton(coordinator, preset_id) for preset_id in range(8)]
    )


class SelectPresetButton(ExampleBaseEntity, ButtonEntity):
    """Set up the Buttons."""

    def __init__(self, coordinator: ExampleCoordinator, preset_id: int) -> None:
        """Initialize coordinator."""
        super().__init__(coordinator)
        self._preset_id = preset_id

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"action-{self._preset_id}"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.coordinator.mac}-action-{self._preset_id}"

    async def async_press(self):
        """Return unique id."""
        # Your action logic here
        await self.coordinator.api.select_preset(self._preset_id)
