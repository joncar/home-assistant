"""Config flow for the LiteJet lighting system."""
import logging
from typing import Any, Dict, Optional

import pylitejet
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import CONF_DEFAULT_TRANSITION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LiteJetOptionsFlow(config_entries.OptionsFlow):
    """Handle LiteJet options."""

    def __init__(self, config_entry):
        """Initialize LiteJet options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage LiteJet options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEFAULT_TRANSITION,
                        default=self.config_entry.options.get(
                            CONF_DEFAULT_TRANSITION, 0
                        ),
                    ): cv.positive_int,
                }
            ),
        )


class LiteJetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """LiteJet config flow."""

    async def async_step_user(self, user_input):
        """Create a LiteJet config entry based upon user input."""
        if self.hass.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        errors = {}
        if user_input is not None:
            port = user_input.get(CONF_PORT)
            try:
                system = pylitejet.LiteJet(port)
                system.close()
                okay = True
            except Exception:
                errors[CONF_PORT] = "open_failed"
                okay = False

            if okay:
                return self.async_create_entry(
                    title=port,
                    data={CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PORT): str}),
            errors=errors,
        )

    async def async_step_import(self, import_data):
        """Import litejet config from configuration.yaml."""
        return self.async_create_entry(title="configuration.yaml", data=import_data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return LiteJetOptionsFlow(config_entry)
