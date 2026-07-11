"""Home Assistant integration for the XGIMI Control Bridge APK."""

from __future__ import annotations

import shlex

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, CONF_SOURCE, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    ACTION_GET_STATUS,
    ACTION_SET_MEMC,
    ACTION_SET_PICTURE_MODE,
    ADB_COMMAND_SERVICE,
    ANDROIDTV_DOMAIN,
    BRIDGE_COMPONENT,
    CONF_MEDIA_PLAYER_ENTITY_ID,
    DOMAIN,
    MEMC_LEVELS,
    PICTURE_MODES,
)

PLATFORMS: list[Platform] = [Platform.SELECT]

ATTR_LEVEL = "level"
ATTR_MODE = "mode"
ATTR_VALUE = "value"

SET_PICTURE_MODE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_MODE): vol.In(PICTURE_MODES),
        vol.Optional(ATTR_VALUE): vol.Coerce(int),
        vol.Optional(CONF_SOURCE): vol.Coerce(int),
    },
    extra=vol.PREVENT_EXTRA,
)

SET_MEMC_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_LEVEL): vol.In(MEMC_LEVELS),
        vol.Optional(ATTR_VALUE): vol.Coerce(int),
        vol.Optional(CONF_SOURCE): vol.Coerce(int),
    },
    extra=vol.PREVENT_EXTRA,
)

GET_STATUS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(CONF_SOURCE): vol.Coerce(int),
    },
    extra=vol.PREVENT_EXTRA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XGIMI Control Bridge from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services once."""
    if hass.services.has_service(DOMAIN, "set_picture_mode"):
        return

    async def set_picture_mode(call: ServiceCall) -> None:
        if ATTR_MODE not in call.data and ATTR_VALUE not in call.data:
            raise HomeAssistantError("Either mode or value is required")

        for entity_id in _entity_ids_from_call(call):
            await async_send_bridge_command(
                hass,
                entity_id,
                ACTION_SET_PICTURE_MODE,
                mode=call.data.get(ATTR_MODE),
                value=call.data.get(ATTR_VALUE),
                source=call.data.get(CONF_SOURCE),
            )

    async def set_memc(call: ServiceCall) -> None:
        if ATTR_LEVEL not in call.data and ATTR_VALUE not in call.data:
            raise HomeAssistantError("Either level or value is required")

        for entity_id in _entity_ids_from_call(call):
            await async_send_bridge_command(
                hass,
                entity_id,
                ACTION_SET_MEMC,
                level=call.data.get(ATTR_LEVEL),
                value=call.data.get(ATTR_VALUE),
                source=call.data.get(CONF_SOURCE),
            )

    async def get_status(call: ServiceCall) -> None:
        for entity_id in _entity_ids_from_call(call):
            await async_send_bridge_command(
                hass,
                entity_id,
                ACTION_GET_STATUS,
                source=call.data.get(CONF_SOURCE),
            )

    hass.services.async_register(
        DOMAIN,
        "set_picture_mode",
        set_picture_mode,
        schema=SET_PICTURE_MODE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "set_memc",
        set_memc,
        schema=SET_MEMC_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "get_status",
        get_status,
        schema=GET_STATUS_SCHEMA,
    )


def _entity_ids_from_call(call: ServiceCall) -> list[str]:
    """Return entity ids from service data or target."""
    entity_ids = call.data.get(ATTR_ENTITY_ID) or call.target.get(ATTR_ENTITY_ID)
    if entity_ids is None:
        raise HomeAssistantError("A media_player target or entity_id is required")
    if isinstance(entity_ids, str):
        return [entity_ids]
    return list(entity_ids)


async def async_send_bridge_command(
    hass: HomeAssistant,
    entity_id: str,
    action: str,
    *,
    mode: str | None = None,
    level: str | None = None,
    value: int | None = None,
    source: int | None = None,
) -> None:
    """Send a broadcast command to the installed Android bridge APK."""
    command = _build_broadcast_command(
        action,
        mode=mode,
        level=level,
        value=value,
        source=source,
    )

    await hass.services.async_call(
        ANDROIDTV_DOMAIN,
        ADB_COMMAND_SERVICE,
        {"command": command},
        blocking=True,
        target={ATTR_ENTITY_ID: entity_id},
    )


def _build_broadcast_command(
    action: str,
    *,
    mode: str | None = None,
    level: str | None = None,
    value: int | None = None,
    source: int | None = None,
) -> str:
    """Build the Android shell broadcast command."""
    parts: list[str] = [
        "am",
        "broadcast",
        "-n",
        BRIDGE_COMPONENT,
        "-a",
        action,
    ]

    if mode is not None:
        parts.extend(["--es", "mode", mode])
    if level is not None:
        parts.extend(["--es", "level", level])
    if value is not None:
        parts.extend(["--ei", "value", str(value)])
    if source is not None:
        parts.extend(["--ei", "source", str(source)])

    return " ".join(shlex.quote(part) for part in parts)


def config_entry_media_player_entity_id(entry: ConfigEntry) -> str:
    """Return the configured Android TV media player entity id."""
    return entry.data[CONF_MEDIA_PLAYER_ENTITY_ID]
