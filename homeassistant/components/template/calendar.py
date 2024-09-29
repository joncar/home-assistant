"""Allows the creation of a calendar."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.calendar import (
    ENTITY_ID_FORMAT,
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME, CONF_STATE, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import config_validation as cv, selector, template
from homeassistant.helpers.device import async_device_info_to_link_from_device_id
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_OBJECT_ID
from .template_entity import TEMPLATE_ENTITY_COMMON_SCHEMA, TemplateEntity

CALENDAR_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_STATE): cv.template_complex,
            vol.Optional(CONF_DEVICE_ID): selector.DeviceSelector(),
        }
    ).extend(TEMPLATE_ENTITY_COMMON_SCHEMA.schema),
)

_LOGGER = logging.getLogger(__name__)


@callback
def _async_create_template_tracking_entities(
    async_add_entities: AddEntitiesCallback,
    hass: HomeAssistant,
    definitions: list[dict],
    unique_id_prefix: str | None,
) -> None:
    """Create the template calendars."""
    calendars = []

    for entity_conf in definitions:
        unique_id = entity_conf.get(CONF_UNIQUE_ID)

        if unique_id and unique_id_prefix:
            unique_id = f"{unique_id_prefix}-{unique_id}"

        calendars.append(
            CalendarTemplate(
                hass,
                entity_conf,
                unique_id,
            )
        )

    async_add_entities(calendars)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the template calendars."""
    if discovery_info is None:
        return
    _async_create_template_tracking_entities(
        async_add_entities,
        hass,
        discovery_info["entities"],
        discovery_info["unique_id"],
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    _options = dict(config_entry.options)
    _options.pop("template_type")
    validated_config = CALENDAR_SCHEMA(_options)
    async_add_entities(
        [CalendarTemplate(hass, validated_config, config_entry.entry_id)]
    )


@callback
def async_create_preview_calendar(
    hass: HomeAssistant, name: str, config: dict[str, Any]
) -> CalendarTemplate:
    """Create a preview calendar."""
    validated_config = CALENDAR_SCHEMA(config | {CONF_NAME: name})
    return CalendarTemplate(hass, validated_config, None)


class CalendarTemplate(TemplateEntity, CalendarEntity):
    """Representation of a Template Calendar."""

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        unique_id: str | None,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(hass, config=config, fallback_name=None, unique_id=unique_id)
        self._template: template.Template = config[CONF_STATE]
        self._attr_device_info = async_device_info_to_link_from_device_id(
            hass,
            config.get(CONF_DEVICE_ID),
        )
        if (object_id := config.get(CONF_OBJECT_ID)) is not None:
            self.entity_id = async_generate_entity_id(
                ENTITY_ID_FORMAT, object_id, hass=hass
            )
        self._events: list[CalendarEvent] = []

    @callback
    def _async_setup_templates(self) -> None:
        """Set up templates."""
        self.add_template_attribute("_state", self._template, None, self._update_state)

        super()._async_setup_templates()

    @callback
    def _update_state(self, result):
        # _LOGGER.error("Updating calendar template state: {}", result)
        super()._update_state(result)
        if isinstance(result, TemplateError):
            self._events = []
            return

        self._events = result

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return next(iter(self._events), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        # events = self._calendar.timeline_tz(start_date.tzinfo).overlapping(
        #    start_date,
        #    end_date,
        # )
        # return [_get_calendar_event(event) for event in events]
        return self._events
