"""Home Assistant integration for the XGIMI Control Bridge APK."""

from __future__ import annotations

import json
import logging
import re
import shlex

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, CONF_SOURCE, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    ACTION_GET_EXT_PQ_SETTINGS,
    ACTION_GET_STATUS,
    ACTION_SET_MEMC,
    ACTION_SET_PICTURE_MODE,
    ADB_COMMAND_AUTOFOCUS,
    ADB_COMMAND_OSD_BACK,
    ADB_COMMAND_OSD_CONFIRM,
    ADB_COMMAND_OSD_PICTURE_MODE_NEXT,
    ADB_COMMAND_OSD_PICTURE_MODE_OPEN,
    ADB_COMMAND_OSD_PICTURE_MODE_PREVIOUS,
    ADB_COMMAND_SERVICE,
    ANDROIDTV_DOMAIN,
    ATTR_ADB_RESPONSE,
    ATTR_LAST_ACTION,
    ATTR_LAST_RESPONSE,
    ATTR_MEMC,
    ATTR_OK,
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
    BRIDGE_COMPONENT,
    CONF_MEDIA_PLAYER_ENTITY_ID,
    DOMAIN,
    MEMC_LEVEL_BY_VALUE,
    MEMC_LEVELS,
    PICTURE_MODE_BY_VALUE,
    PICTURE_MODES,
    PQ_SERVICE_CALL_GET_GLOBAL_NON_AWARE,
    PQ_SERVICE_CALL_GET_HDR_TYPE,
    PQ_SERVICE_CALL_SET_GLOBAL_TRANSACTION,
    PQ_SERVICE_CALL_SET_PERSTREAM_TRANSACTION,
    PQ_SERVICE_NAME,
    SIGNAL_STATUS_UPDATED,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

ATTR_LEVEL = "level"
ATTR_KEY = "key"
ATTR_MODE = "mode"
ATTR_VALUE = "value"

_BROADCAST_DATA_RE = re.compile(
    r'data=(?P<quote>["\'])(?P<data>.*)(?P=quote)', re.DOTALL
)

_NATIVE_PQ_PERSTREAM_KEYS = {
    "AI_PQ",
    "AISR",
    "Brightness",
    "Contrast",
    "Gaming_MJC_Lvl",
    "Hue",
    "Local_Contrast",
    "MJC_Deblur",
    "MJC_Dejudder",
    "MJC_Effect",
}

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

SET_NATIVE_PQ_VALUE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_KEY): cv.string,
        vol.Required(ATTR_VALUE): vol.Any(str, int, float, bool),
    },
    extra=vol.PREVENT_EXTRA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XGIMI Control Bridge from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "data": entry.data,
        "last_response": None,
        "status": {},
    }

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

    async def get_native_pq_status(call: ServiceCall) -> None:
        for entity_id in _entity_ids_from_call(call):
            await async_get_native_pq_status(hass, entity_id)

    async def get_native_hdr_type(call: ServiceCall) -> None:
        for entity_id in _entity_ids_from_call(call):
            await async_get_native_hdr_type(hass, entity_id)

    async def set_native_pq_value(call: ServiceCall) -> None:
        for entity_id in _entity_ids_from_call(call):
            await async_set_native_pq_value(
                hass,
                entity_id,
                call.data[ATTR_KEY],
                call.data[ATTR_VALUE],
            )

    async def get_ext_pq_status(call: ServiceCall) -> None:
        for entity_id in _entity_ids_from_call(call):
            await async_get_ext_pq_status(hass, entity_id)

    async def run_adb_action(call: ServiceCall, command: str, label: str) -> None:
        for entity_id in _entity_ids_from_call(call):
            await async_send_adb_command(
                hass,
                entity_id,
                command,
                status_label=label,
            )

    if not hass.services.has_service(DOMAIN, "set_picture_mode"):
        hass.services.async_register(
            DOMAIN,
            "set_picture_mode",
            set_picture_mode,
            schema=SET_PICTURE_MODE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "set_memc"):
        hass.services.async_register(
            DOMAIN,
            "set_memc",
            set_memc,
            schema=SET_MEMC_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "get_status"):
        hass.services.async_register(
            DOMAIN,
            "get_status",
            get_status,
            schema=GET_STATUS_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "get_native_pq_status"):
        hass.services.async_register(
            DOMAIN,
            "get_native_pq_status",
            get_native_pq_status,
            schema=GET_STATUS_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "get_native_hdr_type"):
        hass.services.async_register(
            DOMAIN,
            "get_native_hdr_type",
            get_native_hdr_type,
            schema=GET_STATUS_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "set_native_pq_value"):
        hass.services.async_register(
            DOMAIN,
            "set_native_pq_value",
            set_native_pq_value,
            schema=SET_NATIVE_PQ_VALUE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "get_ext_pq_status"):
        hass.services.async_register(
            DOMAIN,
            "get_ext_pq_status",
            get_ext_pq_status,
            schema=GET_STATUS_SCHEMA,
        )
    adb_actions = {
        "autofocus": (ADB_COMMAND_AUTOFOCUS, "autofocus"),
        "open_picture_mode_osd": (
            ADB_COMMAND_OSD_PICTURE_MODE_OPEN,
            "open_picture_mode_osd",
        ),
        "osd_picture_mode_previous": (
            ADB_COMMAND_OSD_PICTURE_MODE_PREVIOUS,
            "picture_mode_previous",
        ),
        "osd_picture_mode_next": (
            ADB_COMMAND_OSD_PICTURE_MODE_NEXT,
            "picture_mode_next",
        ),
        "osd_confirm": (ADB_COMMAND_OSD_CONFIRM, "osd_confirm"),
        "osd_back": (ADB_COMMAND_OSD_BACK, "osd_back"),
    }
    for service_name, (command, label) in adb_actions.items():
        if hass.services.has_service(DOMAIN, service_name):
            continue

        async def adb_action(
            call: ServiceCall,
            adb_command: str = command,
            status_label: str = label,
        ) -> None:
            await run_adb_action(call, adb_command, status_label)

        hass.services.async_register(
            DOMAIN,
            service_name,
            adb_action,
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
    previous_response = _adb_response_from_entity(hass, entity_id)
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

    raw_response = _adb_response_from_entity(hass, entity_id)
    parsed_response = _parse_broadcast_response(raw_response)

    if raw_response == previous_response and action == ACTION_GET_STATUS:
        _LOGGER.debug(
            "ADB response for %s did not change after status command: %s",
            entity_id,
            raw_response,
        )

    _update_matching_entries(
        hass,
        entity_id,
        action,
        raw_response,
        parsed_response,
        mode=mode,
        level=level,
        value=value,
        source=source,
    )


async def async_get_native_pq_status(hass: HomeAssistant, entity_id: str) -> None:
    """Read the native MediaTek PQ status JSON via Android's service command."""
    raw_response, pq_json, pq_settings = await async_read_native_pq_settings(hass, entity_id)
    _update_matching_entries_with_native_pq(
        hass,
        entity_id,
        raw_response,
        pq_json,
        pq_settings,
    )


async def async_get_native_hdr_type(hass: HomeAssistant, entity_id: str) -> None:
    """Read native MediaTek HDR type status."""
    await hass.services.async_call(
        ANDROIDTV_DOMAIN,
        ADB_COMMAND_SERVICE,
        {"command": PQ_SERVICE_CALL_GET_HDR_TYPE},
        blocking=True,
        target={ATTR_ENTITY_ID: entity_id},
    )

    raw_response = _adb_response_from_entity(hass, entity_id)
    words = _parse_service_call_words(raw_response)
    decoded = _decode_two_single_value_arrays(words)
    for entry_id, runtime_data in hass.data.get(DOMAIN, {}).items():
        config_data = runtime_data["data"]
        if config_data[CONF_MEDIA_PLAYER_ENTITY_ID] != entity_id:
            continue

        runtime_data[ATTR_LAST_RESPONSE] = raw_response
        status = dict(runtime_data.get("status", {}))
        status[ATTR_OK] = decoded is not None
        if decoded is not None:
            _status_code, return_code, hdr_type = decoded
            status[ATTR_PQ_HDR_TYPE] = hdr_type
            status["pq_hdr_type_return_code"] = return_code
        runtime_data["status"] = status
        async_dispatcher_send(hass, f"{SIGNAL_STATUS_UPDATED}_{entry_id}")


async def async_read_native_pq_settings(
    hass: HomeAssistant,
    entity_id: str,
) -> tuple[str | None, str | None, dict | None]:
    """Read the native MediaTek PQ status JSON without updating entities."""
    await hass.services.async_call(
        ANDROIDTV_DOMAIN,
        ADB_COMMAND_SERVICE,
        {"command": PQ_SERVICE_CALL_GET_GLOBAL_NON_AWARE},
        blocking=True,
        target={ATTR_ENTITY_ID: entity_id},
    )

    raw_response = _adb_response_from_entity(hass, entity_id)
    pq_json = _parse_service_call_utf16_string(raw_response)
    pq_settings = _parse_json_object(pq_json)
    return raw_response, pq_json, pq_settings


async def async_set_native_pq_value(
    hass: HomeAssistant,
    entity_id: str,
    key: str,
    value: str | int | float | bool,
) -> None:
    """Set one MediaTek PQ key and refresh status."""
    parsed_value = _parse_service_value(value)
    payload = json.dumps({key: parsed_value}, separators=(",", ":"))
    command = _build_native_pq_set_command(key, payload)

    await hass.services.async_call(
        ANDROIDTV_DOMAIN,
        ADB_COMMAND_SERVICE,
        {"command": command},
        blocking=True,
        target={ATTR_ENTITY_ID: entity_id},
    )

    raw_response = _adb_response_from_entity(hass, entity_id)
    words = _parse_service_call_words(raw_response)
    if len(words) < 2 or words[0] != 0 or words[1] != 0:
        raise HomeAssistantError(
            f"Native PQ write failed for {key}: {raw_response or 'empty response'}"
        )

    _LOGGER.info("Native PQ %s set to %r", key, parsed_value)
    await async_get_native_pq_status(hass, entity_id)


async def async_get_ext_pq_status(hass: HomeAssistant, entity_id: str) -> None:
    """Read MediaTek ExtService PQ status through the bridge APK."""
    await async_send_bridge_command(hass, entity_id, ACTION_GET_EXT_PQ_SETTINGS)


async def async_send_adb_command(
    hass: HomeAssistant,
    entity_id: str,
    command: str,
    *,
    status_label: str | None = None,
) -> None:
    """Send a plain Android TV ADB command and store its response."""
    await hass.services.async_call(
        ANDROIDTV_DOMAIN,
        ADB_COMMAND_SERVICE,
        {"command": command},
        blocking=True,
        target={ATTR_ENTITY_ID: entity_id},
    )

    raw_response = _adb_response_from_entity(hass, entity_id)
    for entry_id, runtime_data in hass.data.get(DOMAIN, {}).items():
        config_data = runtime_data["data"]
        if config_data[CONF_MEDIA_PLAYER_ENTITY_ID] != entity_id:
            continue

        runtime_data[ATTR_LAST_RESPONSE] = raw_response
        status = dict(runtime_data.get("status", {}))
        status[ATTR_OK] = _adb_command_response_looks_ok(raw_response)
        if status_label is not None:
            status[ATTR_LAST_ACTION] = status_label
        runtime_data["status"] = status
        async_dispatcher_send(hass, f"{SIGNAL_STATUS_UPDATED}_{entry_id}")


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


def _build_native_pq_set_command(key: str, payload: str) -> str:
    """Build a native MediaTek PQ service call for a single key."""
    if key in _NATIVE_PQ_PERSTREAM_KEYS:
        return _build_native_pq_set_perstream_command(payload)
    return _build_native_pq_set_global_command(payload)


def _build_native_pq_set_global_command(payload: str) -> str:
    """Build a native MediaTek PQ setPqParamsByGlobal service call."""
    parts = [
        "service",
        "call",
        PQ_SERVICE_NAME,
        str(PQ_SERVICE_CALL_SET_GLOBAL_TRANSACTION),
        "s16",
        payload,
    ]
    return " ".join(shlex.quote(part) for part in parts)


def _build_native_pq_set_perstream_command(payload: str, pq_id: int = 0) -> str:
    """Build a native MediaTek PQ setPqParams perstream service call."""
    parts = [
        "service",
        "call",
        PQ_SERVICE_NAME,
        str(PQ_SERVICE_CALL_SET_PERSTREAM_TRANSACTION),
        "i32",
        str(pq_id),
        "s16",
        payload,
    ]
    return " ".join(shlex.quote(part) for part in parts)


def _adb_response_from_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Return the latest Android TV ADB response attribute for an entity."""
    state = hass.states.get(entity_id)
    if state is None:
        return None
    response = state.attributes.get(ATTR_ADB_RESPONSE)
    return response if isinstance(response, str) else None


def _parse_broadcast_response(raw_response: str | None) -> dict | None:
    """Parse the JSON payload returned by am broadcast."""
    if not raw_response:
        return None

    stripped = raw_response.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    match = _BROADCAST_DATA_RE.search(stripped)
    if match is None:
        return None

    data = match.group("data").replace(r"\"", '"')
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        _LOGGER.debug("Could not parse XGIMI broadcast data payload: %s", data)
        return None


def _parse_service_call_utf16_string(raw_response: str | None) -> str | None:
    """Extract the first UTF-16 string payload from Android service call output."""
    words = _parse_service_call_words(raw_response)

    if len(words) < 5:
        return None

    # Parcel layout observed for getGlobalNonAwarePqSetting:
    # status, return-vector-size, return-code, string-vector-size, string-length, UTF-16 data...
    if words[1] != 1 or words[3] != 1:
        return None

    string_length = words[4]
    chars: list[str] = []
    for word in words[5:]:
        for shift in (0, 16):
            codepoint = (word >> shift) & 0xFFFF
            if codepoint:
                chars.append(chr(codepoint))
            if len(chars) >= string_length:
                return "".join(chars)
    return "".join(chars) if chars else None


def _parse_service_call_words(raw_response: str | None) -> list[int]:
    """Extract hexadecimal parcel words from Android service call output."""
    if not raw_response:
        return []

    words: list[int] = []
    for token in raw_response.replace("'", " ").replace(")", " ").split():
        if token.startswith("0x"):
            continue
        try:
            words.append(int(token, 16))
        except ValueError:
            continue
    return words


def _decode_two_single_value_arrays(words: list[int]) -> tuple[int, int, int] | None:
    """Decode AIDL out arrays shaped like return-code[] and value[]."""
    if len(words) < 5 or words[1] != 1 or words[3] != 1:
        return None
    return words[0], words[2], words[4]


def _parse_json_object(raw_json: str | None) -> dict | None:
    """Return a JSON object if raw_json contains one."""
    if not raw_json:
        return None
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        _LOGGER.debug("Could not parse native PQ JSON: %s", raw_json[:250])
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_service_value(value: str | int | float | bool) -> str | int | float | bool:
    """Parse text service values as JSON scalars when possible."""
    if not isinstance(value, str):
        return value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    if isinstance(parsed, str | int | float | bool):
        return parsed
    return value


def _update_matching_entries_with_native_pq(
    hass: HomeAssistant,
    entity_id: str,
    raw_response: str | None,
    pq_json: str | None,
    pq_settings: dict | None,
) -> None:
    """Update stored integration status for entries using native MediaTek PQ data."""
    for entry_id, runtime_data in hass.data.get(DOMAIN, {}).items():
        config_data = runtime_data["data"]
        if config_data[CONF_MEDIA_PLAYER_ENTITY_ID] != entity_id:
            continue

        runtime_data[ATTR_LAST_RESPONSE] = raw_response
        status = dict(runtime_data.get("status", {}))
        status[ATTR_OK] = pq_settings is not None
        status[ATTR_PQ_JSON] = pq_json

        if pq_settings:
            _apply_pq_settings_to_status(status, pq_settings)

        runtime_data["status"] = status
        async_dispatcher_send(hass, f"{SIGNAL_STATUS_UPDATED}_{entry_id}")


def _update_matching_entries(
    hass: HomeAssistant,
    entity_id: str,
    action: str,
    raw_response: str | None,
    parsed_response: dict | None,
    *,
    mode: str | None,
    level: str | None,
    value: int | None,
    source: int | None,
) -> None:
    """Update stored integration status for entries using the target media player."""
    for entry_id, runtime_data in hass.data.get(DOMAIN, {}).items():
        config_data = runtime_data["data"]
        if config_data[CONF_MEDIA_PLAYER_ENTITY_ID] != entity_id:
            continue

        runtime_data[ATTR_LAST_RESPONSE] = raw_response
        status = dict(runtime_data.get("status", {}))

        if parsed_response:
            status[ATTR_OK] = parsed_response.get(ATTR_OK)
            if ATTR_SOURCE in parsed_response:
                status[ATTR_SOURCE] = parsed_response[ATTR_SOURCE]
            if ATTR_PICTURE_MODE in parsed_response:
                status[ATTR_PICTURE_MODE] = _name_from_value(
                    parsed_response[ATTR_PICTURE_MODE], PICTURE_MODE_BY_VALUE
                )
            if ATTR_MEMC in parsed_response:
                status[ATTR_MEMC] = _name_from_value(
                    parsed_response[ATTR_MEMC], MEMC_LEVEL_BY_VALUE
                )
            if "command" in parsed_response and "value" in parsed_response:
                if parsed_response["command"] == ATTR_PICTURE_MODE:
                    status[ATTR_PICTURE_MODE] = _name_from_value(
                        parsed_response["value"], PICTURE_MODE_BY_VALUE
                    )
                if parsed_response["command"] == ATTR_MEMC:
                    status[ATTR_MEMC] = _name_from_value(
                        parsed_response["value"], MEMC_LEVEL_BY_VALUE
                    )
            if parsed_response.get("command") == "ext_pq_settings":
                pq_json = parsed_response.get("json_text")
                pq_settings = _parse_json_object(pq_json)
                status[ATTR_PQ_JSON] = pq_json
                if pq_settings:
                    _apply_pq_settings_to_status(status, pq_settings)
        else:
            status[ATTR_OK] = False

        if action == ACTION_SET_PICTURE_MODE:
            status[ATTR_PICTURE_MODE] = (
                mode if mode is not None else _name_from_value(value, PICTURE_MODE_BY_VALUE)
            )
        if action == ACTION_SET_MEMC:
            status[ATTR_MEMC] = (
                level if level is not None else _name_from_value(value, MEMC_LEVEL_BY_VALUE)
            )
        if source is not None:
            status[ATTR_SOURCE] = source

        runtime_data["status"] = status
        async_dispatcher_send(hass, f"{SIGNAL_STATUS_UPDATED}_{entry_id}")


def _apply_pq_settings_to_status(status: dict, pq_settings: dict) -> None:
    """Copy known MediaTek PQ JSON keys into integration status."""
    status[ATTR_PQ_BACKLIGHT] = pq_settings.get("Backlight")
    status[ATTR_PQ_BRIGHTNESS] = pq_settings.get("Brightness")
    status[ATTR_PQ_CONTRAST] = pq_settings.get("Contrast")
    status[ATTR_PQ_COLOR_SPACE] = pq_settings.get("Color space")
    status[ATTR_PQ_DARK_DETAIL] = pq_settings.get("Dark_Detail")
    status[ATTR_PQ_DYNAMIC_COLOR_BOOSTER] = pq_settings.get("Dynamic_Color_Booster")
    status[ATTR_PQ_FILM_MODE] = pq_settings.get("Film_Mode")
    status[ATTR_PQ_GAMMA] = pq_settings.get("Gamma")
    status[ATTR_PQ_GLOBAL_DIMMING] = pq_settings.get("Global_Dimming")
    status[ATTR_PQ_HDR_MODE] = pq_settings.get("HDR_Mode")
    status[ATTR_PQ_HUE] = pq_settings.get("Hue")
    status[ATTR_PQ_COLOR_TEMPERATURE] = pq_settings.get("Color_Temperature")
    status[ATTR_PQ_AI_PICTURE] = pq_settings.get("AI_PQ")
    status[ATTR_PQ_MEMC_EFFECT] = pq_settings.get("MJC_Effect")
    status[ATTR_PQ_LOCAL_CONTRAST] = pq_settings.get("Local_Contrast")
    status[ATTR_PQ_LOW_LATENCY] = pq_settings.get("Low_Latency")
    status[ATTR_PQ_MPEG_NR] = pq_settings.get("MPEG_NR")
    status[ATTR_PQ_NR] = pq_settings.get("NR")
    status[ATTR_PQ_PICTURE_MODE] = pq_settings.get("Picture_Mode")
    status[ATTR_PQ_SATURATION] = pq_settings.get("Saturation")


def _adb_command_response_looks_ok(raw_response: str | None) -> bool:
    """Return whether a plain ADB command response looks successful."""
    if not raw_response:
        return True
    lowered = raw_response.lower()
    return "exception" not in lowered and "error" not in lowered and "failed" not in lowered


def _name_from_value(value: int | None, names: dict[int, str]) -> str | None:
    """Return a friendly name for a numeric vendor value."""
    if value is None:
        return None
    return names.get(value, str(value))


def config_entry_media_player_entity_id(entry: ConfigEntry) -> str:
    """Return the configured Android TV media player entity id."""
    return entry.data[CONF_MEDIA_PLAYER_ENTITY_ID]


def config_entry_runtime_data(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Return runtime data for a config entry."""
    return hass.data[DOMAIN][entry.entry_id]
