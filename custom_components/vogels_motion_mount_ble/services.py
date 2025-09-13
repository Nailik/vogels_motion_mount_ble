import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    HA_SERVICE_AUTOMOVE_ID,
    HA_SERVICE_DELETE_PRESET,
    HA_SERVICE_DISCONNECT,
    HA_SERVICE_DISTANCE_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_DEFAULT_PRESET_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_NAME_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_PRESET_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_TV_ON_OFF_DETECTION_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_DISABLE_CHANNEL_ID,
    HA_SERVICE_MULTI_PIN_FEATURE_START_CALIBRATION_ID,
    HA_SERVICE_NAME_ID,
    HA_SERVICE_PIN_ID,
    HA_SERVICE_PRESET_ID,
    HA_SERVICE_REFRESH_DATA,
    HA_SERVICE_ROTATION_ID,
    HA_SERVICE_SELECT_AUTOMOVE,
    HA_SERVICE_SELECT_PRESET,
    HA_SERVICE_SET_AUTHORISED_USER_PIN,
    HA_SERVICE_SET_DISTANCE,
    HA_SERVICE_SET_FREEZE_PRESET,
    HA_SERVICE_SET_MULTI_PIN_FEATURES,
    HA_SERVICE_SET_NAME,
    HA_SERVICE_SET_PRESET,
    HA_SERVICE_SET_ROTATION,
    HA_SERVICE_SET_SUPERVISIOR_PIN,
    HA_SERVICE_SET_TV_WIDTH,
    HA_SERVICE_TV_WIDTH_ID,
)
from .utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


def async_setup_services(hass: HomeAssistant):
    """Set up my integration services."""
    _LOGGER.debug("async_setup_services called ")
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

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_DISTANCE,
        _set_distance_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_ROTATION,
        _set_rotation_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_TV_WIDTH,
        _set_tv_width_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SELECT_AUTOMOVE,
        _set_automove_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_FREEZE_PRESET,
        _set_freeze_preset_service,
    )

    hass.services.async_register(
        DOMAIN,
        HA_SERVICE_SET_MULTI_PIN_FEATURES,
        _set_multi_pin_features,
    )

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


async def _refresh_data_service(call: ServiceCall) -> None:
    _LOGGER.debug("Refresh data service called with data: %s", call.data)
    await get_coordinator(call).api.refresh_data()


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


async def _set_distance_service(call: ServiceCall) -> None:
    _LOGGER.debug("Set distance service called with data: %s", call.data)
    await get_coordinator(call).api.set_distance(call.data[HA_SERVICE_DISTANCE_ID])


async def _set_rotation_service(call: ServiceCall) -> None:
    _LOGGER.debug("Set rotation service called with data: %s", call.data)
    await get_coordinator(call).api.set_rotation(call.data[HA_SERVICE_ROTATION_ID])


async def _set_tv_width_service(call: ServiceCall) -> None:
    _LOGGER.debug("Set tv width called with data: %s", call.data)
    await get_coordinator(call).api.set_tv_width(call.data[HA_SERVICE_TV_WIDTH_ID])


async def _set_automove_service(call: ServiceCall) -> None:
    _LOGGER.debug("Set automove service called with data: %s", call.data)
    await get_coordinator(call).api.set_automove(call.data[HA_SERVICE_AUTOMOVE_ID])


async def _set_freeze_preset_service(call: ServiceCall) -> None:
    _LOGGER.debug("Set freeze service called with data: %s", call.data)
    await get_coordinator(call).api.set_freeze_preset(call.data[HA_SERVICE_PRESET_ID])


async def _set_multi_pin_features(call: ServiceCall) -> None:
    _LOGGER.debug(
        "Set multi pin features change presets service called with data: %s", call.data
    )
    await get_coordinator(call).api.set_multi_pin_features(
        change_presets=call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_PRESET_ID),
        change_name=call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_NAME_ID),
        disable_channel=call.data.get(HA_SERVICE_MULTI_PIN_FEATURE_DISABLE_CHANNEL_ID),
        change_tv_on_off_detection=call.data.get(
            HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_TV_ON_OFF_DETECTION_ID
        ),
        change_default_position=call.data.get(
            HA_SERVICE_MULTI_PIN_FEATURE_CHANGE_DEFAULT_PRESET_ID
        ),
        start_calibration=call.data.get(
            HA_SERVICE_MULTI_PIN_FEATURE_START_CALIBRATION_ID
        ),
    )


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
