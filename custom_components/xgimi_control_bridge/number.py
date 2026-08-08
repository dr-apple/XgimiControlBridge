"""Number entities for native XGIMI / MediaTek PQ values."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import (
    async_set_native_pq_value,
    config_entry_media_player_entity_id,
    config_entry_runtime_data,
)
from .const import (
    ATTR_PQ_BACKLIGHT,
    ATTR_PQ_BRIGHTNESS,
    ATTR_PQ_CONTRAST,
    DOMAIN,
    SIGNAL_STATUS_UPDATED,
)


@dataclass(frozen=True)
class NativePqNumberDescription:
    """Description for one native PQ number entity."""

    key: str
    name: str
    status_key: str
    pq_key: str
    native_min_value: float
    native_max_value: float
    native_step: float = 1
    native_unit_of_measurement: str | None = None


NATIVE_PQ_NUMBERS: tuple[NativePqNumberDescription, ...] = (
    NativePqNumberDescription(
        key="native_pq_backlight",
        name="Native PQ Backlight",
        status_key=ATTR_PQ_BACKLIGHT,
        pq_key="Backlight",
        native_min_value=0,
        native_max_value=100,
        native_unit_of_measurement=PERCENTAGE,
    ),
    NativePqNumberDescription(
        key="native_pq_brightness",
        name="Native PQ Brightness",
        status_key=ATTR_PQ_BRIGHTNESS,
        pq_key="Brightness",
        native_min_value=0,
        native_max_value=100,
    ),
    NativePqNumberDescription(
        key="native_pq_contrast",
        name="Native PQ Contrast",
        status_key=ATTR_PQ_CONTRAST,
        pq_key="Contrast",
        native_min_value=0,
        native_max_value=100,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up native PQ number entities."""
    media_player_entity_id = config_entry_media_player_entity_id(entry)
    async_add_entities(
        XgimiNativePqNumber(entry, media_player_entity_id, description)
        for description in NATIVE_PQ_NUMBERS
    )


class XgimiNativePqNumber(NumberEntity):
    """Number entity backed by native MediaTek PQ service calls."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        media_player_entity_id: str,
        description: NativePqNumberDescription,
    ) -> None:
        """Initialize the native PQ number entity."""
        self._entry = entry
        self._media_player_entity_id = media_player_entity_id
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_name = description.name
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_native_value = None

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

    async def async_set_native_value(self, value: float) -> None:
        """Set the native PQ value."""
        numeric_value = float(value)
        if numeric_value.is_integer():
            parsed_value: int | float = int(numeric_value)
        else:
            parsed_value = numeric_value

        await async_set_native_pq_value(
            self.hass,
            self._media_player_entity_id,
            self._description.pq_key,
            parsed_value,
        )
        self._attr_native_value = parsed_value
        self.async_write_ha_state()

    def _handle_status_update(self) -> None:
        """Update the number value from stored native PQ status."""
        status = config_entry_runtime_data(self.hass, self._entry).get("status", {})
        value = status.get(self._description.status_key)
        if isinstance(value, int | float):
            self._attr_native_value = value
        elif isinstance(value, str):
            try:
                self._attr_native_value = float(value)
            except ValueError:
                return
        self.schedule_update_ha_state()
