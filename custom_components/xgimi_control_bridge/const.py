"""Constants for the XGIMI Control Bridge integration."""

from __future__ import annotations

DOMAIN = "xgimi_control_bridge"

CONF_MEDIA_PLAYER_ENTITY_ID = "media_player_entity_id"

ATTR_ADB_RESPONSE = "adb_response"
ATTR_LAST_ACTION = "last_action"
ATTR_LAST_RESPONSE = "last_response"
ATTR_MEMC = "memc"
ATTR_OK = "ok"
ATTR_OSD_PICTURE_MODE = "osd_picture_mode"
ATTR_PICTURE_MODE = "picture_mode"
ATTR_PQ_AI_PICTURE = "pq_ai_picture"
ATTR_PQ_BACKLIGHT = "pq_backlight"
ATTR_PQ_BRIGHTNESS = "pq_brightness"
ATTR_PQ_COLOR_TEMPERATURE = "pq_color_temperature"
ATTR_PQ_CONTRAST = "pq_contrast"
ATTR_PQ_COLOR_SPACE = "pq_color_space"
ATTR_PQ_DARK_DETAIL = "pq_dark_detail"
ATTR_PQ_DYNAMIC_COLOR_BOOSTER = "pq_dynamic_color_booster"
ATTR_PQ_FILM_MODE = "pq_film_mode"
ATTR_PQ_GAMMA = "pq_gamma"
ATTR_PQ_GLOBAL_DIMMING = "pq_global_dimming"
ATTR_PQ_HDR_MODE = "pq_hdr_mode"
ATTR_PQ_HDR_TYPE = "pq_hdr_type"
ATTR_PQ_HUE = "pq_hue"
ATTR_PQ_JSON = "pq_json"
ATTR_PQ_LOCAL_CONTRAST = "pq_local_contrast"
ATTR_PQ_LOW_LATENCY = "pq_low_latency"
ATTR_PQ_MEMC_EFFECT = "pq_memc_effect"
ATTR_PQ_MPEG_NR = "pq_mpeg_nr"
ATTR_PQ_NR = "pq_nr"
ATTR_PQ_PICTURE_MODE = "pq_picture_mode"
ATTR_PQ_SATURATION = "pq_saturation"
ATTR_SOURCE = "source"

ANDROIDTV_DOMAIN = "androidtv"
ADB_COMMAND_SERVICE = "adb_command"

BRIDGE_COMPONENT = "de.drapple.xgimi/.XgimiCommandReceiver"
ACTION_SET_PICTURE_MODE = "de.drapple.xgimi.SET_PICTURE_MODE"
ACTION_SET_MEMC = "de.drapple.xgimi.SET_MEMC"
ACTION_GET_STATUS = "de.drapple.xgimi.GET_STATUS"
ACTION_GET_EXT_PQ_SETTINGS = "de.drapple.xgimi.GET_EXT_PQ_SETTINGS"

ADB_COMMAND_AUTOFOCUS = "service call xgimi.hardware.gmpf.IProjectorFocusManager/default 3 i32 2"
ADB_COMMAND_OSD_BACK = "input keyevent KEYCODE_BACK"
ADB_COMMAND_OSD_CONFIRM = "input keyevent KEYCODE_DPAD_CENTER"
ADB_COMMAND_OSD_PICTURE_MODE_NEXT = "input keyevent KEYCODE_DPAD_RIGHT"
ADB_COMMAND_OSD_PICTURE_MODE_PREVIOUS = "input keyevent KEYCODE_DPAD_LEFT"
ADB_COMMAND_OSD_PICTURE_MODE_OPEN = (
    "am start -n com.mediatek.tv.settings/.displayandsound.picture.PictureActivity "
    "--es PictureHotKey picture_mode"
)

PQ_SERVICE_CALL_GET_GLOBAL_NON_AWARE = (
    "service call vendor.mediatek.hardware.pq.IPq/default 54 i32 0 i32 0"
)
PQ_SERVICE_CALL_GET_HDR_TYPE = (
    "service call vendor.mediatek.hardware.pq.IPq/default 59 i32 0 i32 0 i32 0"
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

OSD_PICTURE_MODES = [
    "Lebhaft",
    "Spiel",
    "Film",
    "Standard",
    "Benutzerdefiniert",
]

PICTURE_MODE_BY_VALUE = dict(enumerate(PICTURE_MODES))
MEMC_LEVEL_BY_VALUE = dict(enumerate(MEMC_LEVELS))

SIGNAL_STATUS_UPDATED = f"{DOMAIN}_status_updated"
