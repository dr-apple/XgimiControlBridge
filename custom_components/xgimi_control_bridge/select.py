"""Select entities for XGIMI Control Bridge."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import async_send_bridge_command, config_entry_media_player_entity_id
from .const import (
    ACTION_SET_MEMC,
    ACTION_SET_PICTURE_MODE,
    DOMAIN,
    MEMC_LEVELS,
    PICTURE_MODES,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    entity_id = config_entry_media_player_entity_id(entry)
    async_add_entities(
        [
            XgimiBridgeSelect(
                entry,
                entity_id,
                "picture_mode",
                "Picture Mode",
                PICTURE_MODES,
                ACTION_SET_PICTURE_MODE,
                "mode",
            ),
            XgimiBridgeSelect(
                entry,
                entity_id,
                "memc",
                "MEMC",
                MEMC_LEVELS,
                ACTION_SET_MEMC,
                "level",
            ),
        ]
    )


class XgimiBridgeSelect(SelectEntity):
    """Optimistic select entity backed by an ADB broadcast command."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        media_player_entity_id: str,
        key: str,
        name: str,
        options: list[str],
        action: str,
        extra_name: str,
    ) -> None:
        """Initialize the select entity."""
        self._entry = entry
        self._media_player_entity_id = media_player_entity_id
        self._action = action
        self._extra_name = extra_name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_options = options
        self._attr_current_option = None

    @property
    def device_info(self):
        """Return device information for the bridge controls."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "XGIMI Control Bridge",
            "manufacturer": "XGIMI",
            "model": "Control Bridge",
        }

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        kwargs = {self._extra_name: option}
        await async_send_bridge_command(
            self.hass,
            self._media_player_entity_id,
            self._action,
            **kwargs,
        )
        self._attr_current_option = option
        self.async_write_ha_state()
