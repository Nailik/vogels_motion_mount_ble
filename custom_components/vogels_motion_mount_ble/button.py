"""Button entities to define actions for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_DEVICE_ID,
    HA_SERVICE_SELECT_PRESET,
    HA_SERVICE_SELECT_PRESET_ID,
)
from .coordinator import VogelsMotionMountBleCoordinator

_LOGGER = logging.getLogger(__name__)


async def _select_preset_service(call: ServiceCall) -> None:
    """My first service."""
    device_registry = dr.async_get(call.hass)
    device = device_registry.async_get(call.data[HA_SERVICE_DEVICE_ID])

    _LOGGER.info(
        "Device %s is linked to config entries: %s",
        call.data[HA_SERVICE_DEVICE_ID],
        list(device.config_entries),
    )

    entry_id = next(iter(device.config_entries))
    coordinator: VogelsMotionMountBleCoordinator = call.hass.data[DOMAIN].get(entry_id)

    await coordinator.api.select_preset(call.data[HA_SERVICE_SELECT_PRESET_ID])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Buttons."""
    coordinator: VogelsMotionMountBleCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SELECT_PRESET,
        _select_preset_service,
    )

    # Add one SelectPresetButton for each preset_id from 0 to 7 inclusive
    async_add_entities(
        [SelectPresetButton(coordinator, preset_id) for preset_id in range(8)]
    )


class SelectPresetButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Buttons."""

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_id: int
    ) -> None:
        """Initialize coordinator."""
        super().__init__(coordinator)
        self._preset_id = preset_id

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"Select preset {self._preset_id}"

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
