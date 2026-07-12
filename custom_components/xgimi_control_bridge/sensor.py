"""Sensor entities for XGIMI Control Bridge."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import config_entry_runtime_data
from .const import (
    ATTR_LAST_RESPONSE,
    ATTR_MEMC,
    ATTR_OK,
    ATTR_PICTURE_MODE,
    ATTR_SOURCE,
    DOMAIN,
    SIGNAL_STATUS_UPDATED,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    async_add_entities(
        [
            XgimiBridgeSensor(entry, "picture_mode", "Picture Mode", ATTR_PICTURE_MODE),
            XgimiBridgeSensor(entry, "memc", "MEMC", ATTR_MEMC),
            XgimiBridgeSensor(entry, "source", "Source", ATTR_SOURCE),
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
            self._attr_native_value = runtime_data.get("status", {}).get(
                self._status_key
            )
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return extra attributes for verbose values."""
        if self._from_runtime_root and self._last_raw_value is not None:
            return {"raw": self._last_raw_value}
        return None
