"""Config flow for Railway integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RailwayApiClient, RailwayAuthError, RailwayConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): str,
    }
)


class RailwayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Railway."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN]

            session = async_get_clientsession(self.hass)
            client = RailwayApiClient(api_token, session)

            try:
                me = await client.async_get_me()
                account_id = me.get("id")
                account_name = me.get("name") or me.get("email", "Railway Account")

                if not account_id:
                    errors["base"] = "invalid_auth"
                else:
                    # Use account ID as unique identifier
                    await self.async_set_unique_id(account_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=account_name,
                        data={
                            CONF_API_TOKEN: api_token,
                            "account_id": account_id,
                            "account_name": account_name,
                        },
                    )

            except RailwayAuthError:
                errors["base"] = "invalid_auth"
            except RailwayConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "create_token_url": "https://railway.com/account/tokens"
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthorization."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthorization confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN]

            session = async_get_clientsession(self.hass)
            client = RailwayApiClient(api_token, session)

            try:
                me = await client.async_get_me()
                account_id = me.get("id")

                if not account_id:
                    errors["base"] = "invalid_auth"
                else:
                    reauth_entry = self._get_reauth_entry()
                    return self.async_update_reload_and_abort(
                        reauth_entry,
                        data={
                            **reauth_entry.data,
                            CONF_API_TOKEN: api_token,
                        },
                    )

            except RailwayAuthError:
                errors["base"] = "invalid_auth"
            except RailwayConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
