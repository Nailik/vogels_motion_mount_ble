"""Number entities to define properties that can be changed for Vogels Motion Mount BLE entities."""

import logging

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VogelsMotionMountBleConfigEntry
from .api import VogelsMotionMountPinSettings
from .base import VogelsMotionMountBleBaseEntity, VogelsMotionMountBlePresetBaseEntity
from .const import (
    DOMAIN,
    HA_SERVICE_NAME_ID,
    HA_SERVICE_SET_NAME,
    HA_SERVICE_SET_AUTHORISED_USER_PIN,
    HA_SERVICE_SET_SUPERVISIOR_PIN,
    HA_SERVICE_PIN_ID,
)
from .coordinator import VogelsMotionMountBleCoordinator
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def _set_name(call: ServiceCall) -> None:
    _LOGGER.debug("Set name service called with data: %s", call.data)
    await get_coordinator(call).api.set_name(call.data[HA_SERVICE_NAME_ID])


async def _set_authorised_user_pin(call: ServiceCall) -> None:
    _LOGGER.debug("Set authorised user pin service called with data: %s", call.data)
    await get_coordinator(call).api.set_authorised_user_pin(
        call.data[HA_SERVICE_PIN_ID]
    )


async def _set_supervisior_pin(call: ServiceCall) -> None:
    _LOGGER.debug("Set supervisior pin service called with data: %s", call.data)
    await get_coordinator(call).api.set_supervisior_pin(call.data[HA_SERVICE_PIN_ID])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VogelsMotionMountBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the TextEntities for name, preset names and pins."""
    coordinator: VogelsMotionMountBleCoordinator = config_entry.runtime_data.coordinator

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_NAME,
        _set_name,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_AUTHORISED_USER_PIN,
        _set_authorised_user_pin,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_SUPERVISIOR_PIN,
        _set_supervisior_pin,
    )

    async_add_entities(
        [
            NameText(coordinator),
            AuthorisedUserPinText(coordinator),
            SupervisiorPinText(coordinator),
        ]
        + [PresetNameText(coordinator, preset_index) for preset_index in range(7)]
    )


class NameText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    _attr_unique_id = "name"
    _attr_translation_key = _attr_unique_id
    _attr_native_min = 1
    _attr_native_max = 20

    @property
    def native_value(self):
        """Return the state of the entity."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.name

    async def async_set_value(self, value: str) -> None:
        """Set the name value from the UI."""
        await self.coordinator.api.set_name(value)


class PresetNameText(VogelsMotionMountBlePresetBaseEntity, TextEntity):
    """Implementation of a sensor."""

    def __init__(
        self, coordinator: VogelsMotionMountBleCoordinator, preset_index: int
    ) -> None:
        """Initialize unique_id because it's derived from preset_index."""
        super().__init__(coordinator, preset_index)
        self._attr_translation_placeholders = {
            "name": preset_index,
        }
        # TODO self._attr_unique_id = f"preset_{preset_index}_name"
        self._attr_translation_key = "preset_name_custom"
        self._attr_native_min = 1
        self._attr_native_max = 20  # TODO correct max length?

    @property
    def native_value(self):
        """Return the current value."""
        if self._preset:
            return self._preset.name
        return None

    async def async_set_value(self, value: str) -> None:
        """Set the preset name value from the UI."""
        await self.coordinator.api.set_preset(
            preset_index=self._preset_index, name=value
        )


class AuthorisedUserPinText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    _attr_unique_id = "authorised_user_pin"
    _attr_translation_key = _attr_unique_id
    _attr_native_min = 4
    _attr_native_max = 4

    @property
    def native_value(self):
        """Return the state of the entity."""
        if self.coordinator.data is None:
            return None
        return "    "

    async def async_set_value(self, value: str) -> None:
        """Set the authoised user pin value from the UI."""
        await self.coordinator.api.set_authorised_user_pin(value)


class SupervisiorPinText(VogelsMotionMountBleBaseEntity, TextEntity):
    """Implementation of a the Name Text."""

    # TODO only available if there is already an authorised user pin
    _attr_unique_id = "supervisior_pin"
    _attr_translation_key = _attr_unique_id
    _attr_native_min = 4
    _attr_native_max = 4

    @property
    def native_value(self):
        """Return the state of the entity."""
        if self.coordinator.data is None:
            return None
        return "    "

    @property
    def available(self) -> bool:
        """Set availability of this index of Preset entity based if the preset is available in the data."""
        return (
            self.coordinator.data.pin_setting
            is not VogelsMotionMountPinSettings.Deactivated
        )

    async def async_set_value(self, value: str) -> None:
        """Set the supervisior pin value from the UI."""
        await self.coordinator.api.set_supervisior_pin(value)
