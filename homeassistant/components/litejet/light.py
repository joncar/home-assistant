"""Support for LiteJet lights."""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_TRANSITION,
    LightEntity,
)

from .const import CONF_DEFAULT_TRANSITION, DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_NUMBER = "number"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""

    system = hass.data[DOMAIN]

    devices = []
    for i in system.loads():
        name = system.get_load_name(i)
        devices.append(LiteJetLight(config_entry, system, i, name))
    async_add_devices(devices, True)


class LiteJetLight(LightEntity):
    """Representation of a single LiteJet light."""

    def __init__(self, config_entry, lj, i, name):
        """Initialize a LiteJet light."""
        self._config_entry = config_entry
        self._lj = lj
        self._index = i
        self._brightness = 0
        self._name = name

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        self._lj.on_load_activated(self._index, self._on_load_changed)
        self._lj.on_load_deactivated(self._index, self._on_load_changed)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        self._lj.unsubscribe(self._on_load_changed)

    def _on_load_changed(self):
        """Handle state changes."""
        _LOGGER.debug("Updating due to notification for %s", self._name)
        self.schedule_update_ha_state(True)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION

    @property
    def name(self):
        """Return the light's name."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique identifier for this light."""
        return str(self._index)

    @property
    def brightness(self):
        """Return the light's brightness."""
        return self._brightness

    @property
    def is_on(self):
        """Return if the light is on."""
        return self._brightness != 0

    @property
    def should_poll(self):
        """Return that lights do not require polling."""
        return False

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return {ATTR_NUMBER: self._index}

    def turn_on(self, **kwargs):
        """Turn on the light."""
        is_complex = False
        brightness = 99
        transition = self._config_entry.options.get(CONF_DEFAULT_TRANSITION, 0)

        if ATTR_BRIGHTNESS in kwargs:
            is_complex = True
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 255 * 99)

        if ATTR_TRANSITION in kwargs:
            is_complex = True
            transition = kwargs[ATTR_TRANSITION]

        if is_complex:
            self._lj.activate_load_at(self._index, brightness, int(transition))
        else:
            self._lj.activate_load(self._index)

    def turn_off(self, **kwargs):
        """Turn off the light."""
        is_complex = False
        transition = self._config_entry.options.get(CONF_DEFAULT_TRANSITION, 0)

        if ATTR_TRANSITION in kwargs:
            is_complex = True
            transition = kwargs[ATTR_TRANSITION]

        if is_complex:
            self._lj.activate_load_at(self._index, 0, transition)
        else:
            self._lj.deactivate_load(self._index)

    def update(self):
        """Retrieve the light's brightness from the LiteJet system."""
        self._brightness = int(self._lj.get_load_level(self._index) / 99 * 255)
