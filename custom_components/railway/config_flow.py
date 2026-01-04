"""Config flow for Railway integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import RailwayApiClient, RailwayAuthError, RailwayConnectionError
from .const import CONF_SCAN_INTERVAL, CONF_TOKEN_TYPE, DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_TOKEN_TYPE, default="personal"): SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": "personal", "label": "Personal Token"},
                    {"value": "team", "label": "Team Token"},
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)

SCAN_INTERVAL_OPTIONS = [
    {"value": "5", "label": "5 minutes"},
    {"value": "10", "label": "10 minutes"},
    {"value": "15", "label": "15 minutes (default)"},
    {"value": "30", "label": "30 minutes"},
    {"value": "60", "label": "60 minutes"},
]


class RailwayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Railway."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RailwayOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN]
            token_type = user_input.get(CONF_TOKEN_TYPE, "personal")

            _LOGGER.debug("Attempting to validate Railway API token (type: %s)", token_type)

            session = async_get_clientsession(self.hass)
            client = RailwayApiClient(api_token, session, token_type)

            try:
                me = await client.async_get_me()
                account_id = me.get("id")
                account_name = me.get("name") or me.get("email", "Railway Account")

                _LOGGER.debug("Got account info: id=%s, name=%s", account_id, account_name)

                if not account_id:
                    _LOGGER.error("No account ID returned from Railway API")
                    errors["base"] = "invalid_auth"
                else:
                    # Use account ID as unique identifier
                    await self.async_set_unique_id(account_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=account_name,
                        data={
                            CONF_API_TOKEN: api_token,
                            CONF_TOKEN_TYPE: token_type,
                            "account_id": account_id,
                            "account_name": account_name,
                        },
                    )

            except RailwayAuthError as err:
                _LOGGER.error("Railway authentication failed: %s", err)
                errors["base"] = "invalid_auth"
            except RailwayConnectionError as err:
                _LOGGER.error("Railway connection failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during Railway setup")
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
            token_type = user_input.get(CONF_TOKEN_TYPE, "personal")

            session = async_get_clientsession(self.hass)
            client = RailwayApiClient(api_token, session, token_type)

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
                            CONF_TOKEN_TYPE: token_type,
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


class RailwayOptionsFlowHandler(OptionsFlow):
    """Handle Railway options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=str(current_interval),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=SCAN_INTERVAL_OPTIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )
