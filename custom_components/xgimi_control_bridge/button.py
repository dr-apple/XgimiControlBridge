"""Button entities for XGIMI Control Bridge."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    async_get_native_pq_status,
    async_send_bridge_command,
    config_entry_media_player_entity_id,
)
from .const import ACTION_GET_STATUS, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    async_add_entities(
        [
            XgimiRefreshStatusButton(entry),
            XgimiRefreshNativePqStatusButton(entry),
        ]
    )


class XgimiRefreshStatusButton(ButtonEntity):
    """Button that refreshes the XGIMI bridge status."""

    _attr_has_entity_name = True
    _attr_name = "Refresh Status"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh_status"
        self._media_player_entity_id = config_entry_media_player_entity_id(entry)

    @property
    def device_info(self):
        """Return device information for the bridge controls."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "XGIMI Control Bridge",
            "manufacturer": "XGIMI",
            "model": "Control Bridge",
        }

    async def async_press(self) -> None:
        """Refresh status through the Android bridge APK."""
        await async_send_bridge_command(
            self.hass,
            self._media_player_entity_id,
            ACTION_GET_STATUS,
        )


class XgimiRefreshNativePqStatusButton(ButtonEntity):
    """Button that refreshes native MediaTek PQ status."""

    _attr_has_entity_name = True
    _attr_name = "Refresh Native PQ Status"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh_native_pq_status"
        self._media_player_entity_id = config_entry_media_player_entity_id(entry)

    @property
    def device_info(self):
        """Return device information for the bridge controls."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "XGIMI Control Bridge",
            "manufacturer": "XGIMI",
            "model": "Control Bridge",
        }

    async def async_press(self) -> None:
        """Refresh status through the native MediaTek PQ service."""
        await async_get_native_pq_status(self.hass, self._media_player_entity_id)
