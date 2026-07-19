"""Select entities for XGIMI Control Bridge."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    async_set_osd_picture_mode,
    async_set_native_pq_value,
    async_send_bridge_command,
    config_entry_media_player_entity_id,
    config_entry_runtime_data,
)
from .const import (
    ACTION_SET_MEMC,
    ATTR_MEMC,
    ATTR_OSD_PICTURE_MODE,
    ATTR_PQ_AI_PICTURE,
    ATTR_PQ_COLOR_TEMPERATURE,
    ATTR_PQ_GAMMA,
    ATTR_PQ_LOCAL_CONTRAST,
    ATTR_PQ_MEMC_EFFECT,
    DOMAIN,
    MEMC_LEVELS,
    OSD_PICTURE_MODES,
    SIGNAL_STATUS_UPDATED,
)


NATIVE_PQ_SELECTS: tuple[dict[str, object], ...] = (
    {
        "key": "native_pq_gamma",
        "name": "Native PQ Gamma",
        "status_key": ATTR_PQ_GAMMA,
        "pq_key": "Gamma",
        "options": ["Dark", "Middle", "Bright"],
    },
    {
        "key": "native_pq_color_temperature",
        "name": "Native PQ Color Temperature",
        "status_key": ATTR_PQ_COLOR_TEMPERATURE,
        "pq_key": "Color_Temperature",
        "options": ["Standard", "Warm", "Cold", "Cool", "User"],
    },
    {
        "key": "native_pq_ai_picture",
        "name": "Native PQ AI Picture",
        "status_key": ATTR_PQ_AI_PICTURE,
        "pq_key": "AI_PQ",
        "options": ["Off", "On"],
    },
    {
        "key": "native_pq_memc",
        "name": "Native PQ MEMC",
        "status_key": ATTR_PQ_MEMC_EFFECT,
        "pq_key": "MJC_Effect",
        "options": ["Off", "Low", "Middle", "High", "User"],
    },
    {
        "key": "native_pq_local_contrast",
        "name": "Native PQ Local Contrast",
        "status_key": ATTR_PQ_LOCAL_CONTRAST,
        "pq_key": "Local_Contrast",
        "options": ["Off", "Low", "Middle", "High"],
    },
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
                "memc",
                "MEMC",
                MEMC_LEVELS,
                ACTION_SET_MEMC,
                "level",
            ),
            XgimiOsdPictureModeSelect(entry, entity_id),
            *[
                XgimiNativePqSelect(entry, entity_id, description)
                for description in NATIVE_PQ_SELECTS
            ],
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
        self._status_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_options = options
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Register for status updates."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_STATUS_UPDATED}_{self._entry.entry_id}",
                self._handle_status_update,
            )
        )
        self._handle_status_update()

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

    def _handle_status_update(self) -> None:
        """Update the current option from stored status."""
        status = config_entry_runtime_data(self.hass, self._entry).get("status", {})
        option = status.get(ATTR_MEMC)
        if option in self.options:
            self._attr_current_option = option
        self.schedule_update_ha_state()


class XgimiOsdPictureModeSelect(SelectEntity):
    """Optimistic select backed by visible OSD navigation."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, media_player_entity_id: str) -> None:
        """Initialize the OSD picture mode select."""
        self._entry = entry
        self._media_player_entity_id = media_player_entity_id
        self._attr_unique_id = f"{entry.entry_id}_osd_picture_mode"
        self._attr_translation_key = "osd_picture_mode"
        self._attr_name = "OSD Picture Mode"
        self._attr_options = OSD_PICTURE_MODES
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Register for status updates."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_STATUS_UPDATED}_{self._entry.entry_id}",
                self._handle_status_update,
            )
        )
        self._handle_status_update()

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
        """Select a visible OSD picture mode by stepping through the OSD."""
        await async_set_osd_picture_mode(
            self.hass,
            self._media_player_entity_id,
            option,
        )
        self._attr_current_option = option
        self.async_write_ha_state()

    def _handle_status_update(self) -> None:
        """Update the current option from stored OSD status."""
        status = config_entry_runtime_data(self.hass, self._entry).get("status", {})
        option = status.get(ATTR_OSD_PICTURE_MODE)
        if option in self.options:
            self._attr_current_option = option
        self.schedule_update_ha_state()


class XgimiNativePqSelect(SelectEntity):
    """Select entity backed by native MediaTek PQ service calls."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        media_player_entity_id: str,
        description: dict[str, object],
    ) -> None:
        """Initialize the native PQ select entity."""
        self._entry = entry
        self._media_player_entity_id = media_player_entity_id
        self._status_key = str(description["status_key"])
        self._pq_key = str(description["pq_key"])
        self._attr_unique_id = f"{entry.entry_id}_{description['key']}"
        self._attr_translation_key = str(description["key"])
        self._attr_name = str(description["name"])
        self._attr_options = list(description["options"])
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Register for status updates."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_STATUS_UPDATED}_{self._entry.entry_id}",
                self._handle_status_update,
            )
        )
        self._handle_status_update()

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
        """Select a native PQ option."""
        await async_set_native_pq_value(
            self.hass,
            self._media_player_entity_id,
            self._pq_key,
            option,
        )
        self._attr_current_option = option
        self.async_write_ha_state()

    def _handle_status_update(self) -> None:
        """Update the current option from stored native PQ status."""
        status = config_entry_runtime_data(self.hass, self._entry).get("status", {})
        option = status.get(self._status_key)
        if option in self.options:
            self._attr_current_option = option
        elif isinstance(option, str):
            self._attr_current_option = option
        self.schedule_update_ha_state()
