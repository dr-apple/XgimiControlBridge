"""Home Assistant 2026.8 compatibility tests."""

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xgimi_control_bridge import (
    _entity_ids_from_call,
    _parse_broadcast_response,
    _parse_service_value,
)
from custom_components.xgimi_control_bridge.const import (
    CONF_MEDIA_PLAYER_ENTITY_ID,
    DOMAIN,
)


def test_service_call_entity_targets(hass: HomeAssistant) -> None:
    """Service targets use the entity IDs carried in modern ServiceCall data."""
    call = ServiceCall(
        hass,
        DOMAIN,
        "get_status",
        {ATTR_ENTITY_ID: ["media_player.projector"]},
    )

    assert _entity_ids_from_call(call) == ["media_player.projector"]


def test_response_and_scalar_parsing() -> None:
    """ADB responses and service values keep their supported scalar types."""
    assert _parse_broadcast_response('{"ok":true,"source":1}') == {
        "ok": True,
        "source": 1,
    }
    assert _parse_service_value("42") == 42
    assert _parse_service_value("true") is True
    assert _parse_service_value("plain text") == "plain text"


async def test_setup_creates_entities_on_one_config_entry_device(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """All bridge controls attach to a device owned by only this config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="XGIMI Control Bridge",
        unique_id="media_player.projector",
        data={CONF_MEDIA_PLAYER_ENTITY_ID: "media_player.projector"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(entities) == 49
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    assert devices[0].config_entry_id == entry.entry_id

    assert await hass.config_entries.async_unload(entry.entry_id)
