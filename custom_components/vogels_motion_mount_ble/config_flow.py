"""Config flow for Integration 101 Template integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from .api import API, APIConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Data to be input by the user in the config flow.
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(
            CONF_NAME, description={"suggested_value": "Vogel's Motion Mount"}
        ): str,
        vol.Optional(CONF_PIN): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=9999, mode=selector.NumberSelectorMode.BOX
            )
        ),
    }
)


def prefilledForm(name: str) -> vol.Schema:
    """Return a form schema with prefilled values for host and name."""
    # Return a schema where CONF_HOST is shown but not editable (using selector.TextSelector with disabled=True)
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=name): str,
            vol.Optional(CONF_PIN): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )


class VogelsMotionMountConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for VogelsMotionMount Integration."""

    VERSION = 1
    _input_data: dict[str, Any]

    def __init__(self):
        """Setup data."""
        self.discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await self.setup_entry(user_input)
            if isinstance(result, dict) and "type" in result:
                return result
            errors = result

        if user_input is not None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str,
                        vol.Required(
                            CONF_NAME,
                            description={"suggested_value": "Vogel's Motion Mount"},
                            default=user_input.get(CONF_NAME),
                        ): str,
                        vol.Optional(
                            CONF_PIN, default=user_input.get(CONF_PIN)
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                            )
                        ),
                    }
                ),
                errors=errors,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(
                        CONF_NAME,
                        description={"suggested_value": "Vogel's Motion Mount"},
                    ): str,
                    vol.Optional(CONF_PIN): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_bluetooth(self, discovery_info):
        """Handle a bluetooth device being discovered."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self.discovery_info = discovery_info

        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None):
        """Confirm adding the discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await self.setup_entry(
                data={
                    CONF_HOST: self.discovery_info.address,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_PIN: user_input.get(CONF_PIN),
                }
            )
            _LOGGER.debug("setup_entry result: %s", result)
            if isinstance(result, dict) and "type" in result:
                _LOGGER.debug("setup_entry return ConfigFlowResult: %s", result)
                return result
            errors = result

        if user_input is not None:
            # If no user input, show the form with prefilled values
            return self.async_show_form(
                step_id="confirm",
                errors=errors,
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default=user_input[CONF_NAME]): str,
                        vol.Optional(
                            CONF_PIN, default=user_input.get(CONF_PIN)
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                            )
                        ),
                    }
                ),
            )

        _LOGGER.debug(
            "async_show_form self.discovery_info.advertisement.local_namet: %s",
            self.discovery_info.advertisement.local_name,
        )
        return self.async_show_form(
            step_id="confirm",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self.discovery_info.advertisement.local_name
                    ): str,
                    vol.Optional(CONF_PIN): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=9999, mode=selector.NumberSelectorMode.BOX
                        )
                    ),
                }
            ),
        )

    async def validate_user_input(self, data: dict[str, Any]) -> None:
        """Validate the user input by testing connection."""
        _LOGGER.debug("Validating user input: %s", data)
        mac = data[CONF_HOST]

        # Create an API instance and try to connect.
        api = API(mac, data.get(CONF_PIN), lambda *_, **__: None)
        try:
            await api.testConnect()
        except APIConnectionError as err:
            raise CannotConnect from err

    async def setup_entry(
        self, data: dict[str, Any]
    ) -> dict[str, str] | ConfigFlowResult:
        """Setup the entry from user data."""
        _LOGGER.debug("Setting up entry with data: %s", data)
        errors: dict[str, str] = {}
        try:
            await self.validate_user_input(data)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            errors["base"] = "unknown"

        _LOGGER.debug("Setting async_set_unique_id: %s", data)
        if not errors:
            # Validation was successful, so create a unique id for this instance of your integration
            # and create the config entry.
            await self.async_set_unique_id(data[CONF_HOST])
            self._abort_if_unique_id_configured()
            _LOGGER.debug("Setting async_create_entry: %s", data)
            return self.async_create_entry(title=data[CONF_NAME], data=data)

        return errors


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
