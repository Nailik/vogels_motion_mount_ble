"""Button entities to define actions for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_PRESET_ID,
    HA_SERVICE_REFRESH_DATA,
    HA_SERVICE_SELECT_PRESET,
)
from .coordinator import VogelsMotionMountBleCoordinator
from .preset_base import VogelsMotionMountBlePresetBaseEntity
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)

async def _refresh_data_service(call: ServiceCall) -> None:
    _LOGGER.debug("_refresh_data_service called with data: %s", call.data)
    await get_coordinator(call).api.refreshData()

async def _select_preset_service(call: ServiceCall) -> None:
    _LOGGER.debug("_select_preset_service called with data: %s", call.data)
    await get_coordinator(call).api.select_preset(call.data[HA_SERVICE_PRESET_ID])

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the RefreshData and SelectPreset buttons."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_REFRESH_DATA,
        _refresh_data_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SELECT_PRESET,
        _select_preset_service,
    )

    async_add_entities(
        [RefreshDataButton(coordinator), SelectPresetDefaultButton(coordinator)]
        # Add one SelectPresetButton for each preset_id from 0 to 7 inclusive
        + [SelectPresetButton(coordinator, preset_index) for preset_index in range(7)]
    )


class RefreshDataButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to refresh data."""

    _attr_unique_id = "refresh_data"
    _attr_translation_key = _attr_unique_id

    async def async_press(self):
        """Execute data refresh."""
        await self.coordinator.api.refreshData()


class SelectPresetDefaultButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Buttons to select the default preset."""

    _attr_unique_id = "selec_preset_default"
    _attr_translation_key = _attr_unique_id

    async def async_press(self):
        """Select the default preset with id 0."""
        await self.coordinator.api.select_preset(0)


class SelectPresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to select the custom presets."""

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"selec_preset_{preset_index}"
        self._attr_translation_key = "selec_preset_custom"


    async def async_press(self):
        """Select a custom preset by it's id."""
        await self.coordinator.api.select_preset(
            self.coordinator.data.presets[self._preset_index].id
        )
