"""
Support for EverLights lights.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.everlights/
"""
import logging
import socket
import random

import voluptuous as vol

from homeassistant.const import CONF_DEVICES, CONF_NAME
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_HS_COLOR, ATTR_EFFECT, ATTR_WHITE_VALUE,
    EFFECT_COLORLOOP, EFFECT_RANDOM, SUPPORT_BRIGHTNESS, SUPPORT_EFFECT,
    SUPPORT_COLOR, SUPPORT_WHITE_VALUE, Light, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession

REQUIREMENTS = ['pyeverlights==0.1.0']

_LOGGER = logging.getLogger(__name__)

CONF_AUTOMATIC_ADD = 'automatic_add'
ATTR_MODE = 'mode'

DOMAIN = 'everlights'

SUPPORT_EVERLIGHTS = (SUPPORT_EFFECT | SUPPORT_COLOR)

DEVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_DEVICES, default={}): {cv.string: DEVICE_SCHEMA},
    vol.Optional(CONF_AUTOMATIC_ADD, default=False):  cv.boolean,
})

def color_rgb_to_int(r: int, g: int, b: int) -> int:
    """Return a RGB color as an integer."""
    return r*256*256+g*256+b

def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the EverLights lights from a config entry."""
    import pyeverlights
    lights = []

    api = pyeverlights.EverLights(config_entry.data['ipaddr'],
                                  async_get_clientsession(hass))

    status = api.get_status()

    async_add_devices([
        EverLightsLight(api, pyeverlights.ZONE_1, status)
        EverLightsLight(api, pyeverlights.ZONE_2, status)
    ])


class EverLightsLight(Light):
    """Representation of a Flux light."""

    def __init__(self, api, channel, status):
        """Initialize the light."""
        self._api = None
        self._channel = channel
        self._status = status
        self._error_reported = False
        self._rgb = [255, 255, 255]

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._status['mac']+'-'+str(self._channel)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._status is not None

    @property
    def name(self):
        """Return the name of the device if any."""
        return 'EverLights '+self._status['mac']+' Zone '+str(self._channel)

    @property
    def should_poll(self):
        """Returns true because polling is required."""
        return True

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._status['ch'+str(self._channel)+'Active'] == 1

    @property
    def hs_color(self):
        """Return the color property."""
        return color_util.color_RGB_to_hs(*self._rgb)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_EVERLIGHTS

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        # TODO
        return []

    async def async_turn_on(self, **kwargs):
        """Turn the specified or all lights on."""

        hs_color = kwargs.get(ATTR_HS_COLOR)

        if hs_color:
            rgb = color_util.color_hs_to_RGB(*hs_color)
        else:
            rgb = None

        effect = kwargs.get(ATTR_EFFECT)

        # Show warning if effect set with rgb
        if effect and rgb:
            _LOGGER.warning("Color is ignored when"
                            " an effect is specified")

        # Preserve color on brightness/white level change
        if rgb is None:
            rgb = self._rgb

        await self._api.set_pattern(self._channel, [color_rgb_to_int(*rgb)])

        self._rgb = rgb

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._api.clear_pattern(self._channel)

    async def async_update(self):
        """Synchronize state with control box."""
        status = await self._api.get_status()
