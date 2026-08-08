"""Config flow for XGIMI Control Bridge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.const import Platform
from homeassistant.helpers import selector

from homeassistant import config_entries

from .const import CONF_MEDIA_PLAYER_ENTITY_ID, DOMAIN


class XgimiControlBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for XGIMI Control Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entity_id = user_input[CONF_MEDIA_PLAYER_ENTITY_ID]
            await self.async_set_unique_id(entity_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="XGIMI Control Bridge",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_MEDIA_PLAYER_ENTITY_ID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=Platform.MEDIA_PLAYER)
                )
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
