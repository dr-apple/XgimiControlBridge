"""Button entities for XGIMI Control Bridge."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import (
    async_get_ext_pq_status,
    async_get_native_hdr_type,
    async_get_native_pq_status,
    async_send_adb_command,
    async_send_bridge_command,
    config_entry_media_player_entity_id,
)
from .const import (
    ACTION_GET_STATUS,
    ADB_COMMAND_AUTOFOCUS,
    ADB_COMMAND_OSD_BACK,
    ADB_COMMAND_OSD_CONFIRM,
    ADB_COMMAND_OSD_PICTURE_MODE_NEXT,
    ADB_COMMAND_OSD_PICTURE_MODE_OPEN,
    ADB_COMMAND_OSD_PICTURE_MODE_PREVIOUS,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up button entities."""
    async_add_entities(
        [
            XgimiRefreshAllStatusButton(entry),
            XgimiRefreshStatusButton(entry),
            XgimiRefreshNativePqStatusButton(entry),
            XgimiRefreshExtPqStatusButton(entry),
            XgimiAdbCommandButton(
                entry,
                "autofocus",
                "Autofocus",
                ADB_COMMAND_AUTOFOCUS,
                "autofocus",
            ),
            XgimiAdbCommandButton(
                entry,
                "osd_picture_mode_open",
                "Open Picture Mode OSD",
                ADB_COMMAND_OSD_PICTURE_MODE_OPEN,
                "open_picture_mode_osd",
            ),
            XgimiAdbCommandButton(
                entry,
                "osd_picture_mode_previous",
                "Picture Mode Previous",
                ADB_COMMAND_OSD_PICTURE_MODE_PREVIOUS,
                "picture_mode_previous",
            ),
            XgimiAdbCommandButton(
                entry,
                "osd_picture_mode_next",
                "Picture Mode Next",
                ADB_COMMAND_OSD_PICTURE_MODE_NEXT,
                "picture_mode_next",
            ),
            XgimiAdbCommandButton(
                entry,
                "osd_confirm",
                "OSD Confirm",
                ADB_COMMAND_OSD_CONFIRM,
                "osd_confirm",
            ),
            XgimiAdbCommandButton(
                entry,
                "osd_back",
                "OSD Back",
                ADB_COMMAND_OSD_BACK,
                "osd_back",
            ),
        ]
    )


class XgimiRefreshAllStatusButton(ButtonEntity):
    """Button that refreshes all stable status paths."""

    _attr_has_entity_name = True
    _attr_name = "Refresh All Status"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh_all_status"
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
        """Refresh bridge and native PQ status."""
        await async_send_bridge_command(
            self.hass,
            self._media_player_entity_id,
            ACTION_GET_STATUS,
        )
        await async_get_native_pq_status(self.hass, self._media_player_entity_id)
        await async_get_native_hdr_type(self.hass, self._media_player_entity_id)


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


class XgimiRefreshExtPqStatusButton(ButtonEntity):
    """Button that refreshes MediaTek ExtService PQ status."""

    _attr_has_entity_name = True
    _attr_name = "Refresh ExtService PQ Status"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh_ext_pq_status"
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
        """Refresh status through the MediaTek ExtService bridge path."""
        await async_get_ext_pq_status(self.hass, self._media_player_entity_id)


class XgimiAdbCommandButton(ButtonEntity):
    """Button that runs one plain ADB command against the configured media player."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        key: str,
        name: str,
        command: str,
        status_label: str,
    ) -> None:
        """Initialize the ADB command button."""
        self._entry = entry
        self._command = command
        self._status_label = status_label
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
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
        """Run the configured ADB command."""
        await async_send_adb_command(
            self.hass,
            self._media_player_entity_id,
            self._command,
            status_label=self._status_label,
        )
