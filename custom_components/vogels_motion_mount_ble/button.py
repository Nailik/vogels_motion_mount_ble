
import logging
from homeassistant.components.button import ButtonEntity
from .base import ExampleBaseEntity
from .const import DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyConfigEntry
from .base import ExampleBaseEntity
from .const import DOMAIN
from .coordinator import ExampleCoordinator
from homeassistant.core import HomeAssistant, ServiceCall, callback
        
_LOGGER = logging.getLogger(__name__)

@callback
def _my_service() -> None:
    """My first service."""
    _LOGGER.info('Received data')

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Buttons."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([MyActionButton(coordinator)])
    hass.services.async_register(DOMAIN,'demo', _my_service)

class MyActionButton(ExampleBaseEntity, ButtonEntity):

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "action"

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.coordinator.mac}-action"

    async def async_press(self):
        # Your action logic here
       await self.coordinator.api.perform_action()
