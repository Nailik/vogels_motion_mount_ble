"""Config flow and options flow for Vogels Motion Mount BLE integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
import re
from typing import Any
from .data import (
    VogelsMotionMountAuthenticationType,
)
from homeassistant.components import bluetooth

import voluptuous as vol
from voluptuous.schema_builder import UNDEFINED

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util import dt as dt_util

from .client import (
    get_permissions,
)
from .const import CONF_ERROR, CONF_MAC, CONF_NAME, CONF_PIN, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of the validation, errors is empty if successful."""

    errors: dict[str, str]
    description_placeholders: dict[str, Any] | None = None


class VogelsMotionMountConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Vogel's MotionMount Integration."""

    VERSION = 1

    _discovery_info: BluetoothServiceInfoBleak | None = None

    def prefilledForm(
        self,
        data: dict[str, Any] | None = None,
        mac_editable: bool = True,
        name_editable: bool = True,
    ) -> vol.Schema:
        """Return a form schema with prefilled values from data."""
        _LOGGER.debug(
            "Load prefilled form with: %s and info %s", data, self._discovery_info
        )
        # Setup Values
        mac = UNDEFINED
        name = UNDEFINED
        pin = UNDEFINED

        # Read values from data if provided
        if data is not None:
            mac = data.get(CONF_MAC, UNDEFINED)
            name = data.get(CONF_NAME, f"Vogel's MotionMount ({mac})")
            pin = data.get(CONF_PIN, UNDEFINED)

        # If discovery_info is set, use its address as the MAC and for the name if not provided
        if self._discovery_info is not None:
            _LOGGER.debug("Set mac not editable")
            mac_editable = False
            mac = self._discovery_info.address
            name = self._discovery_info.name

        # Provide Schema
        return vol.Schema(
            {
                vol.Required(CONF_MAC, default=mac): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        multiline=False,
                        read_only=not mac_editable,
                    )
                ),
                vol.Required(CONF_NAME, default=name): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        multiline=False,
                        read_only=not name_editable,
                    )
                ),
                vol.Optional(CONF_PIN, default=pin): vol.All(
                    NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=9999,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            read_only=False,
                        )
                    ),
                    vol.Coerce(int),
                ),
            },
        )

    async def validate_input(self, user_input: dict[str, Any]) -> ValidationResult:
        """Set up the entry from user data."""
        if not bool(
            re.match(
                r"^([0-9A-Fa-f]{2}([-:])){5}([0-9A-Fa-f]{2})$", user_input[CONF_MAC]
            )
        ):
            _LOGGER.error("Invalid MAC code: %s", user_input[CONF_MAC])
            return ValidationResult({CONF_ERROR: "invalid_mac_code"})

        try:
            device = bluetooth.async_ble_device_from_address(
                hass=self.hass,
                address=user_input[CONF_MAC],
                connectable=True,
            )

            if device is None:
                return ValidationResult({CONF_ERROR: "error_device_not_found"})

            client = await establish_connection(
                client_class=BleakClientWithServiceCache,
                device=device,
                name=device.name or "Unknown Device",
            )

            permissions = await get_permissions(client, user_input.get(CONF_PIN))
            if (
                permissions.auth_status.type
                == VogelsMotionMountAuthenticationType.Wrong
            ):
                if permissions.auth_status.cooldown > 0:
                    retry_time = dt_util.now() + timedelta(
                        seconds=permissions.auth_status.cooldown
                    )
                    return ValidationResult(
                        errors={CONF_ERROR: "error_invalid_authentication_cooldown"},
                        description_placeholders={
                            "retry_at": retry_time.strftime("%Y-%m-%d %H:%M:%S")
                        },
                    )
                return ValidationResult({CONF_ERROR: "error_invalid_authentication"})

            _LOGGER.debug(
                "Successfully tested connection to %s pers %s",
                user_input[CONF_MAC],
                permissions,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Setting Exception: %s", err)
            return ValidationResult(
                errors={CONF_ERROR: "error_unknown"},
                description_placeholders={"error": err},
            )
        return ValidationResult({})

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a bluetooth device being discovered."""
        # Check if the device already exists.
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        _LOGGER.debug("async_step_bluetooth %s", discovery_info)
        self._discovery_info = discovery_info

        return self.async_show_form(
            step_id="user",
            data_schema=self.prefilledForm(),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the entry with unique id if not already configured."""
        _LOGGER.debug("async_step_user %s", user_input)
        result = ValidationResult(errors={})
        if user_input is not None:
            result = await self.validate_input(user_input)
            if not result.errors:
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
            data_schema=self.prefilledForm(data=user_input),
            errors=result.errors,
            description_placeholders=result.description_placeholders,
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        _LOGGER.debug("async_step_reauth %s", user_input)
        result = ValidationResult(errors={})
        config_entry = self._get_reauth_entry()
        if user_input is not None:
            result = await self.validate_input(user_input)
            if not result.errors:
                await self.async_set_unique_id(user_input[CONF_MAC])
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry=self._get_reauth_entry(),
                    data_updates=user_input,
                )
        return self.async_show_form(
            step_id="reauth",
            data_schema=self.prefilledForm(
                data=dict(config_entry.data),
                mac_editable=False,
                name_editable=False,
            ),
            errors=result.errors,
            description_placeholders=result.description_placeholders,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-configuration."""
        _LOGGER.debug("async_step_reconfigure %s", user_input)
        result = ValidationResult(errors={})
        config_entry = self._get_reconfigure_entry()
        if user_input is not None:
            result = await self.validate_input(user_input)
            if not result.errors:
                await self.async_set_unique_id(user_input[CONF_MAC])
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry=self._get_reconfigure_entry(),
                    data_updates=user_input,
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.prefilledForm(
                data=dict(config_entry.data),
                mac_editable=False,
            ),
            errors=result.errors,
            description_placeholders=result.description_placeholders,
        )
