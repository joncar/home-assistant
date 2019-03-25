"""Support for the LiteJet lighting system."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import pylitejet

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_PORT): cv.string})},
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up the LiteJet component."""
    hass.data.setdefault(DOMAIN, {})

    if not hass.config_entries.async_entries(DOMAIN) and config[DOMAIN]:
        # No config entry exists and configuration.yaml config exists, trigger the import flow.
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LiteJet via a config entry."""
    port = entry.data[CONF_PORT]

    try:
        system = pylitejet.LiteJet(port)
    except Exception:
        _LOGGER.error("Error connecting to the LiteJet MCP at %s", port)
        return False

    hass.data[DOMAIN] = system

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a LiteJet config entry."""

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN][entry.entry_id].close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
