"""Sensor entities for XGIMI Control Bridge."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import config_entry_runtime_data
from .const import (
    ATTR_LAST_ACTION,
    ATTR_LAST_RESPONSE,
    ATTR_MEMC,
    ATTR_OK,
    ATTR_OSD_PICTURE_MODE,
    ATTR_PICTURE_MODE,
    ATTR_PQ_AI_PICTURE,
    ATTR_PQ_BACKLIGHT,
    ATTR_PQ_BRIGHTNESS,
    ATTR_PQ_COLOR_SPACE,
    ATTR_PQ_COLOR_TEMPERATURE,
    ATTR_PQ_CONTRAST,
    ATTR_PQ_DARK_DETAIL,
    ATTR_PQ_DYNAMIC_COLOR_BOOSTER,
    ATTR_PQ_FILM_MODE,
    ATTR_PQ_GAMMA,
    ATTR_PQ_GLOBAL_DIMMING,
    ATTR_PQ_HDR_MODE,
    ATTR_PQ_HDR_TYPE,
    ATTR_PQ_HUE,
    ATTR_PQ_JSON,
    ATTR_PQ_LOCAL_CONTRAST,
    ATTR_PQ_LOW_LATENCY,
    ATTR_PQ_MEMC_EFFECT,
    ATTR_PQ_MPEG_NR,
    ATTR_PQ_NR,
    ATTR_PQ_PICTURE_MODE,
    ATTR_PQ_SATURATION,
    ATTR_SOURCE,
    DOMAIN,
    SIGNAL_STATUS_UPDATED,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    async_add_entities(
        [
            XgimiBridgeSensor(entry, "picture_mode", "Picture Mode", ATTR_PICTURE_MODE),
            XgimiBridgeSensor(entry, "memc", "MEMC", ATTR_MEMC),
            XgimiBridgeSensor(entry, "source", "Source", ATTR_SOURCE),
            XgimiBridgeSensor(
                entry,
                "osd_picture_mode",
                "OSD Picture Mode",
                ATTR_OSD_PICTURE_MODE,
            ),
            XgimiBridgeSensor(entry, "last_action", "Last Action", ATTR_LAST_ACTION),
            XgimiBridgeSensor(
                entry,
                "pq_backlight",
                "Native PQ Backlight",
                ATTR_PQ_BACKLIGHT,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_brightness",
                "Native PQ Brightness",
                ATTR_PQ_BRIGHTNESS,
            ),
            XgimiBridgeSensor(entry, "pq_contrast", "Native PQ Contrast", ATTR_PQ_CONTRAST),
            XgimiBridgeSensor(entry, "pq_saturation", "Native PQ Saturation", ATTR_PQ_SATURATION),
            XgimiBridgeSensor(entry, "pq_hue", "Native PQ Hue", ATTR_PQ_HUE),
            XgimiBridgeSensor(entry, "pq_gamma", "Native PQ Gamma", ATTR_PQ_GAMMA),
            XgimiBridgeSensor(
                entry,
                "pq_color_temperature",
                "Native PQ Color Temperature",
                ATTR_PQ_COLOR_TEMPERATURE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_ai_picture",
                "Native PQ AI Picture",
                ATTR_PQ_AI_PICTURE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_hdr_mode",
                "Native PQ HDR Mode",
                ATTR_PQ_HDR_MODE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_hdr_type",
                "Native PQ HDR Type",
                ATTR_PQ_HDR_TYPE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_color_space",
                "Native PQ Color Space",
                ATTR_PQ_COLOR_SPACE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_memc_effect",
                "Native PQ MEMC",
                ATTR_PQ_MEMC_EFFECT,
            ),
            XgimiBridgeSensor(entry, "pq_nr", "Native PQ NR", ATTR_PQ_NR),
            XgimiBridgeSensor(entry, "pq_mpeg_nr", "Native PQ MPEG NR", ATTR_PQ_MPEG_NR),
            XgimiBridgeSensor(
                entry,
                "pq_local_contrast",
                "Native PQ Local Contrast",
                ATTR_PQ_LOCAL_CONTRAST,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_low_latency",
                "Native PQ Low Latency",
                ATTR_PQ_LOW_LATENCY,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_global_dimming",
                "Native PQ Global Dimming",
                ATTR_PQ_GLOBAL_DIMMING,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_dark_detail",
                "Native PQ Dark Detail",
                ATTR_PQ_DARK_DETAIL,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_dynamic_color_booster",
                "Native PQ Dynamic Color Booster",
                ATTR_PQ_DYNAMIC_COLOR_BOOSTER,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_film_mode",
                "Native PQ Film Mode",
                ATTR_PQ_FILM_MODE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_picture_mode",
                "Native PQ Picture Mode",
                ATTR_PQ_PICTURE_MODE,
            ),
            XgimiBridgeSensor(
                entry,
                "pq_json",
                "Native PQ JSON",
                ATTR_PQ_JSON,
            ),
            XgimiBridgeSensor(entry, "last_ok", "Last Command OK", ATTR_OK),
            XgimiBridgeSensor(
                entry,
                "last_adb_response",
                "Last ADB Response",
                ATTR_LAST_RESPONSE,
                from_runtime_root=True,
            ),
        ]
    )


class XgimiBridgeSensor(SensorEntity):
    """Sensor backed by parsed Android broadcast responses."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        key: str,
        name: str,
        status_key: str,
        *,
        from_runtime_root: bool = False,
    ) -> None:
        """Initialize the sensor entity."""
        self._entry = entry
        self._status_key = status_key
        self._from_runtime_root = from_runtime_root
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_native_value = None
        self._last_raw_value = None

    @property
    def device_info(self):
        """Return device information for the bridge controls."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "XGIMI Control Bridge",
            "manufacturer": "XGIMI",
            "model": "Control Bridge",
        }

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

    def _handle_status_update(self) -> None:
        """Update sensor state from runtime data."""
        runtime_data = config_entry_runtime_data(self.hass, self._entry)
        if self._from_runtime_root:
            value = runtime_data.get(self._status_key)
            self._last_raw_value = value
            if isinstance(value, str) and len(value) > 250:
                self._attr_native_value = f"{value[:247]}..."
            else:
                self._attr_native_value = value
        else:
            value = runtime_data.get("status", {}).get(self._status_key)
            self._last_raw_value = value
            if isinstance(value, str) and len(value) > 250:
                self._attr_native_value = f"{value[:247]}..."
            else:
                self._attr_native_value = value
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return extra attributes for verbose values."""
        if isinstance(self._last_raw_value, str) and len(self._last_raw_value) > 250:
            return {"raw_length": len(self._last_raw_value)}
        return None
