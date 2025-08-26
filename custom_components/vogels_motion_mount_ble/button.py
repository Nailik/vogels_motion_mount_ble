"""Button entities to define actions for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_DELETE_PRESET,
    HA_SERVICE_DISCONNECT,
    HA_SERVICE_DISTANCE_ID,
    HA_SERVICE_NAME_ID,
    HA_SERVICE_PRESET_ID,
    HA_SERVICE_REFRESH_DATA,
    HA_SERVICE_ROTATION_ID,
    HA_SERVICE_SELECT_PRESET,
    HA_SERVICE_SET_PRESET,
)
from .coordinator import VogelsMotionMountBleCoordinator
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _refresh_data_service(call: ServiceCall) -> None:
    _LOGGER.debug("Refresh data service called with data: %s", call.data)
    await get_coordinator(call).api.refreshData()


async def _disconnect_service(call: ServiceCall) -> None:
    _LOGGER.debug("Disconnect service called with data: %s", call.data)
    await get_coordinator(call).api.disconnect()


async def _select_preset_service(call: ServiceCall) -> None:
    _LOGGER.debug("Select preset service called with data: %s", call.data)
    await get_coordinator(call).api.select_preset(call.data[HA_SERVICE_PRESET_ID])


async def _delete_preset_service(call: ServiceCall) -> None:
    _LOGGER.debug("Delete preset service called with data: %s", call.data)
    await get_coordinator(call).api.delete_preset(call.data[HA_SERVICE_PRESET_ID])


async def _set_preset_service(call: ServiceCall) -> None:
    _LOGGER.debug("Add preset service called with data: %s", call.data)
    await get_coordinator(call).api.set_preset(
        call.data[HA_SERVICE_PRESET_ID],
        call.data[HA_SERVICE_NAME_ID],
        call.data[HA_SERVICE_DISTANCE_ID],
        call.data[HA_SERVICE_ROTATION_ID],
    )


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
        HA_SERVICE_DISCONNECT,
        _disconnect_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SELECT_PRESET,
        _select_preset_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_DELETE_PRESET,
        _delete_preset_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_PRESET,
        _set_preset_service,
    )

    async_add_entities(
        [
            RefreshDataButton(coordinator),
            DisconnectButton(coordinator),
            SelectPresetDefaultButton(coordinator),
        ]
        # Add one SelectPresetButton for each preset_id from 0 to 7 inclusive
        + [
            SelectPresetButton(coordinator, preset_index)
            for preset_index in range(1, 8)
        ]
        # Add one DeletePresetButton for each preset_id from 0 to 7 inclusive
        + [
            DeletePresetButton(coordinator, preset_index)
            for preset_index in range(1, 8)
        ]
        # Add one AddPresetButton for each preset_id from 0 to 7 inclusive
        + [AddPresetButton(coordinator, preset_index) for preset_index in range(1, 8)]
    )


class RefreshDataButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to refresh data."""

    _attr_unique_id = "refresh_data"
    _attr_translation_key = _attr_unique_id

    async def async_press(self):
        """Execute data refresh."""
        await self.coordinator.api.refreshData()


class DisconnectButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Button that provides an action to disconnect data."""

    _attr_unique_id = "disconnect"
    _attr_translation_key = _attr_unique_id

    @property
    def available(self) -> bool:
        """Set availability only if device is connected currently."""
        if self.coordinator.data and self.coordinator.data.connected:
            return True
        return False

    async def async_press(self):
        """Execute disconnect."""
        await self.coordinator.api.disconnect()


class SelectPresetDefaultButton(VogelsMotionMountBleBaseEntity, ButtonEntity):
    """Set up the Buttons to select the default preset."""

    _attr_unique_id = "select_preset_default"
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
        self._attr_unique_id = f"select_preset_{preset_index}"
        self._attr_translation_key = "select_preset_custom"

    async def async_press(self):
        """Select a custom preset by it's index."""
        await self.coordinator.api.select_preset(
            self.coordinator.data.presets[self._preset_index].id
        )


class DeletePresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to delete the custom presets."""

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"delete_preset_{preset_index}"
        self._attr_translation_key = "delete_preset_custom"

    async def async_press(self):
        """Delete a custom preset by it's index."""
        await self.coordinator.api.delete_preset(self._preset_index)


class AddPresetButton(VogelsMotionMountBlePresetBaseEntity, ButtonEntity):
    """Set up the Buttons to add the custom presets."""

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_unique_id = f"add_preset_{preset_index}"
        self._attr_translation_key = "add_preset_custom"

    async def async_press(self):
        """Add a custom preset by it's index with empty data."""
        await self.coordinator.api.set_preset(
            self._preset_index,
            0,
            0,
            f"Preset {self._preset_index}",  # TODO translation
        )

    @property
    def available(self) -> bool:
        """Set availability of this index of Preset entity based on the lengths of presets in the data."""
        if (
            self.coordinator.data
            and self.coordinator.data.presets
            and self._preset_index in self.coordinator.data.presets
            and not self.coordinator.data.presets[self._preset_index]
        ):
            return True
        return False
