"""Support for LiteJet scenes."""
import logging
from typing import Any

from homeassistant.components.scene import Scene

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_NUMBER = "number"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""

    system = hass.data[DOMAIN]

    devices = []
    for i in system.scenes():
        name = system.get_scene_name(i)
        devices.append(LiteJetScene(system, i, name))
    async_add_devices(devices, True)


class LiteJetScene(Scene):
    """Representation of a single LiteJet scene."""

    def __init__(self, lj, i, name):
        """Initialize the scene."""
        self._lj = lj
        self._index = i
        self._name = name

    @property
    def name(self):
        """Return the name of the scene."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique identifier for this scene."""
        return str(self._index)

    @property
    def device_state_attributes(self):
        """Return the device-specific state attributes."""
        return {ATTR_NUMBER: self._index}

    def activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        self._lj.activate_scene(self._index)

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Scenes are only enabled by explicit user choice."""
        return False
