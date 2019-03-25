"""Tests for the litejet component."""
from homeassistant.components import scene, switch
from homeassistant.components.litejet import DOMAIN
from homeassistant.const import CONF_PORT

from tests.common import MockConfigEntry


async def init_integration(hass, use_switch=False, use_scene=False) -> MockConfigEntry:
    """Set up the LiteJet integration in Home Assistant."""

    registry = await hass.helpers.entity_registry.async_get_registry()

    if use_switch:
        registry.async_get_or_create(
            switch.DOMAIN,
            DOMAIN,
            "1",
            suggested_object_id="mock_switch_1",
            disabled_by=None,
        )
        registry.async_get_or_create(
            switch.DOMAIN,
            DOMAIN,
            "2",
            suggested_object_id="mock_switch_2",
            disabled_by=None,
        )

    if use_scene:
        registry.async_get_or_create(
            scene.DOMAIN,
            DOMAIN,
            "1",
            suggested_object_id="mock_scene_1",
            disabled_by=None,
        )

    entry_data = {CONF_PORT: "/dev/mock"}
    entry = MockConfigEntry(domain=DOMAIN, data=entry_data)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry
