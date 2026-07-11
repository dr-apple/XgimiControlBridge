"""Constants for the XGIMI Control Bridge integration."""

from __future__ import annotations

DOMAIN = "xgimi_control_bridge"

CONF_MEDIA_PLAYER_ENTITY_ID = "media_player_entity_id"

ANDROIDTV_DOMAIN = "androidtv"
ADB_COMMAND_SERVICE = "adb_command"

BRIDGE_COMPONENT = "de.drapple.xgimi/.XgimiCommandReceiver"
ACTION_SET_PICTURE_MODE = "de.drapple.xgimi.SET_PICTURE_MODE"
ACTION_SET_MEMC = "de.drapple.xgimi.SET_MEMC"
ACTION_GET_STATUS = "de.drapple.xgimi.GET_STATUS"

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
