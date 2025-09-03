"""Config flow and options flow for Vogels Motion Mount BLE integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from voluptuous.schema_builder import UNDEFINED
from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryBaseFlow,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import (
    API,
    APIConnectionDeviceNotFoundError,
    APIConnectionError,
)
from .const import CONF_ERROR, CONF_MAC, CONF_NAME, CONF_PIN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class VogelsMotionMountUserStepMixin(ConfigEntryBaseFlow):
    """Mixin to provide async_step_user for config and options flow."""

    discovery_info: BluetoothServiceInfoBleak | None = None
    mac_fixed: bool = False

    def prefilledForm(
        self,
        data: dict[str, Any] | None = None,
    ) -> vol.Schema:
        """Return a form schema with prefilled values from data."""
        # Setup Values
        mac = UNDEFINED
        name = UNDEFINED
        pin = UNDEFINED
        preset_subdevice = False

        # Read values from data if provided
        if data is not None:
            mac = data.get(CONF_MAC, UNDEFINED)
            name = data.get(CONF_NAME, f"Vogel's MotionMount ({mac})")
            pin = data.get(CONF_PIN, UNDEFINED)

        # If discovery_info is set, use its address as the MAC and for the name if not provided
        if self.discovery_info is not None:
            mac = self.discovery_info.address
            name = f"Vogel's MotionMount ({mac})" if name == UNDEFINED else name

        # Provide Schema
        return vol.Schema(
            {
                vol.Required(CONF_MAC, default=mac): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                        multiline=False,
                        read_only=self.mac_fixed,
                    )
                ),
                vol.Required(CONF_NAME, default=name): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                        multiline=False,
                    )
                ),
                vol.Optional(CONF_PIN, default=pin): vol.All(
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=9999,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Coerce(int),
                ),
            },
        )

    async def validate_input(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, str] | None:
        """Set up the entry from user data."""
        errors: dict[str, str] = {}
        try:
            await API(
                hass=self.hass,
                mac=user_input[CONF_MAC],
                pin=user_input.get(CONF_PIN),
                callback=lambda *_, **__: None,
            ).test_connection()
            _LOGGER.debug("Successfully tested connection to %s", user_input[CONF_MAC])
        except APIConnectionDeviceNotFoundError as err:
            _LOGGER.error("Setting APIConnectionDeviceNotFoundError: %s", err)
            errors[CONF_ERROR] = "error_device_not_found"
        except ConfigEntryAuthFailed as err:
            _LOGGER.error("Setting APIAuthenticationError: %s", err)
            errors[CONF_ERROR] = "error_invalid_athentication"
        except APIConnectionError as err:
            _LOGGER.error("Setting APIConnectionError: %s", err)
            errors[CONF_ERROR] = "error_cannot_connect"
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Setting Exception: %s", err)
            errors[CONF_ERROR] = "error_unknown"
        return errors


class VogelsMotionMountConfigFlow(
    ConfigFlow, VogelsMotionMountUserStepMixin, domain=DOMAIN
):
    """Handle the config flow for Vogel's MotionMount Integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> VogelsMotionMountOptionsFlowHandler:
        """Create the options flow to change config later on."""
        return VogelsMotionMountOptionsFlowHandler(config_entry)

    async def async_step_bluetooth(self, discovery_info):
        """Handle a bluetooth device being discovered."""
        # Check if the device already exists.
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self.discovery_info = discovery_info

        self.mac_fixed = True
        return self.async_show_form(
            step_id="user",
            data_schema=self.prefilledForm(),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the entry with unique id if not already configured."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self.validate_input(user_input)
            if not errors:
                # Validation was successful, create a unique id and create the config entry.
                await self.async_set_unique_id(user_input[CONF_MAC])
                self._abort_if_unique_id_configured()
                _LOGGER.debug("Create entry with %s", user_input)
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.prefilledForm(user_input),
            errors=errors,
        )


class VogelsMotionMountOptionsFlowHandler(OptionsFlow, VogelsMotionMountUserStepMixin):
    """Update the options via UI."""

    # mac cannot be changed in options flow
    mac_fixed = True

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options update."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self.validate_input(user_input)
            if not errors:
                _LOGGER.debug("Update entry with %s", user_input)
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            return self.async_show_form(
                step_id="init",
                data_schema=self.prefilledForm(user_input),
                errors=errors,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self.prefilledForm(self.config_entry.data),
            errors=errors,
        )
