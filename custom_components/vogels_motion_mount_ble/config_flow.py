"""Config flow and options flow for Vogels Motion Mount BLE integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from voluptuous.schema_builder import UNDEFINED

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import API, APIConnectionDeviceNotFoundError, APIConnectionError
from .const import (
    CONF_CONTROL_PIN,
    CONF_ERROR,
    CONF_MAC,
    CONF_MAINTAIN_CONNECTION,
    CONF_NAME,
    CONF_SETTINGS_PIN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def prefilledForm(
    data: dict[str, Any] | None = None,
    discovery_info: BluetoothServiceInfoBleak | None = None,
) -> vol.Schema:
    """Return a form schema with prefilled values from data."""
    # Setup Values
    mac_fixed = False

    mac = UNDEFINED
    name = UNDEFINED
    maintain_connection = False
    settings_pin = UNDEFINED
    control_pin = UNDEFINED

    # Read values from data if provided
    if data is not None:
        mac = data.get(CONF_MAC, UNDEFINED)
        name = data.get(CONF_NAME, f"Vogel's MotionMount ({mac})")
        maintain_connection = data.get(CONF_MAINTAIN_CONNECTION, False)
        settings_pin = data.get(CONF_SETTINGS_PIN, UNDEFINED)
        control_pin = data.get(CONF_CONTROL_PIN, UNDEFINED)

    # If discovery_info is set, use its address as the MAC and for the name if not provided
    if discovery_info is not None:
        mac = discovery_info.address
        mac_fixed = True
        name = f"Vogel's MotionMount ({mac})" if name == UNDEFINED else name

    # Provide Schema
    return vol.Schema(
        {
            vol.Required(CONF_MAC, default=mac): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                    multiline=False,
                    read_only=mac_fixed,
                )
            ),
            vol.Required(CONF_NAME, default=name): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                    multiline=False,
                )
            ),
            vol.Required(
                CONF_MAINTAIN_CONNECTION, default=maintain_connection
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_SETTINGS_PIN, default=settings_pin
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_CONTROL_PIN, default=control_pin
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                )
            ),
        },
    )


class VogelsMotionMountConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Vogel's MotionMount Integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Set up data to hold discovery info if required."""
        self.discovery_info: BluetoothServiceInfoBleak | None = None

    def prefilledForm(
        self,
        data: dict[str, Any] | None = None,
    ) -> vol.Schema:
        """Return a form schema with prefilled values from data and local discovery info."""
        return prefilledForm(data, self.discovery_info)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> VogelsMotionMountOptionsFlowHandler:
        """Create the options flow to change config later on."""
        return VogelsMotionMountOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step when user adds a device that was not discovered."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Try to set up the entry
            result = await self.setup_entry(user_input)
            # If the result is a ConfigFlowResult, return it directly.
            if isinstance(result, dict) and "type" in result:
                return result
            # If the result is a dictionary, it contains errors.
            errors = result

        # If we reach this point, we either have errors or no user input yet.
        return self.async_show_form(
            step_id="user",
            data_schema=self.prefilledForm(user_input),
            errors=errors,
        )

    async def async_step_bluetooth(self, discovery_info):
        """Handle a bluetooth device being discovered."""

        # Check if the device already exists.
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self.discovery_info = discovery_info

        return self.async_show_form(
            step_id="user",
            data_schema=self.prefilledForm(),
        )

    async def validate_user_input(self, data: dict[str, Any]) -> None:
        """Validate the user input by testing connection, may throw an error if connection fails."""

        # Create an API instance and try to connect.
        await API(
            mac=data[CONF_MAC],
            settings_pin=data.get(CONF_SETTINGS_PIN),
            control_pin=data.get(CONF_CONTROL_PIN),
            callback=lambda *_, **__: None,
        ).test_connection()

    async def setup_entry(
        self, data: dict[str, Any]
    ) -> dict[str, str] | ConfigFlowResult:
        """Set up the entry from user data."""
        errors: dict[str, str] = {}
        try:
            await self.validate_user_input(data)
        except APIConnectionDeviceNotFoundError as err:
            _LOGGER.error("Setting APIConnectionDeviceNotFoundError: %s", err)
            errors[CONF_ERROR] = "error_device_not_found"
        except APIConnectionError as err:
            _LOGGER.error("Setting APIConnectionError: %s", err)
            errors[CONF_ERROR] = "error_cannot_connect"
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Setting Exception: %s", err)
            errors[CONF_ERROR] = "error_unknown"

        if not errors:
            # Validation was successful, create a unique id and create the config entry.
            await self.async_set_unique_id(data[CONF_MAC])
            self._abort_if_unique_id_configured()
            _LOGGER.debug("Setting async_create_entry: %s", data)
            return self.async_create_entry(title=data[CONF_NAME], data=data)

        return errors


class VogelsMotionMountOptionsFlowHandler(OptionsFlow):
    """Update the options via UI."""

    def __init__(self, config_entry) -> None:
        """Store current config entry data in order to populate via ui."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options update."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=prefilledForm(self.config_entry.data),
        )
