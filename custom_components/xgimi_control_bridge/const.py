"""Constants for the XGIMI Control Bridge integration."""

from __future__ import annotations

DOMAIN = "xgimi_control_bridge"

CONF_MEDIA_PLAYER_ENTITY_ID = "media_player_entity_id"

ATTR_ADB_RESPONSE = "adb_response"
ATTR_LAST_RESPONSE = "last_response"
ATTR_MEMC = "memc"
ATTR_OK = "ok"
ATTR_PICTURE_MODE = "picture_mode"
ATTR_PQ_AI_PICTURE = "pq_ai_picture"
ATTR_PQ_BACKLIGHT = "pq_backlight"
ATTR_PQ_BRIGHTNESS = "pq_brightness"
ATTR_PQ_COLOR_TEMPERATURE = "pq_color_temperature"
ATTR_PQ_CONTRAST = "pq_contrast"
ATTR_PQ_GAMMA = "pq_gamma"
ATTR_PQ_JSON = "pq_json"
ATTR_PQ_LOCAL_CONTRAST = "pq_local_contrast"
ATTR_PQ_MEMC_EFFECT = "pq_memc_effect"
ATTR_PQ_PICTURE_MODE = "pq_picture_mode"
ATTR_SOURCE = "source"

ANDROIDTV_DOMAIN = "androidtv"
ADB_COMMAND_SERVICE = "adb_command"

BRIDGE_COMPONENT = "de.drapple.xgimi/.XgimiCommandReceiver"
ACTION_SET_PICTURE_MODE = "de.drapple.xgimi.SET_PICTURE_MODE"
ACTION_SET_MEMC = "de.drapple.xgimi.SET_MEMC"
ACTION_GET_STATUS = "de.drapple.xgimi.GET_STATUS"
ACTION_GET_EXT_PQ_SETTINGS = "de.drapple.xgimi.GET_EXT_PQ_SETTINGS"

PQ_SERVICE_CALL_GET_GLOBAL_NON_AWARE = (
    "service call vendor.mediatek.hardware.pq.IPq/default 54 i32 0 i32 0"
)
PQ_SERVICE_CALL_SET_GLOBAL_TRANSACTION = 160
PQ_SERVICE_CALL_SET_PERSTREAM_TRANSACTION = 159
PQ_SERVICE_NAME = "vendor.mediatek.hardware.pq.IPq/default"

PICTURE_MODES = [
    "bright",
    "standard",
    "soft",
    "user",
    "game",
    "auto",
    "pc",
    "movie",
    "natural",
    "sports",
]

MEMC_LEVELS = [
    "off",
    "low",
    "middle",
    "high",
    "bypass",
]

PICTURE_MODE_BY_VALUE = dict(enumerate(PICTURE_MODES))
MEMC_LEVEL_BY_VALUE = dict(enumerate(MEMC_LEVELS))

SIGNAL_STATUS_UPDATED = f"{DOMAIN}_status_updated"
