"""Config flow for Claude Usage integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ClaudeUsageApiClient,
    ClaudeUsageApiError,
    ClaudeUsageAuthError,
    ClaudeUsageConnectionError,
)
from .const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USE_SSL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ClaudeUsageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Claude Usage."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the connection
            try:
                await self._test_connection(user_input)
            except ClaudeUsageConnectionError:
                errors["base"] = "cannot_connect"
            except ClaudeUsageAuthError:
                errors["base"] = "invalid_auth"
            except ClaudeUsageApiError:
                errors["base"] = "unknown"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on host:port
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Claude Usage ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_API_KEY): str,
                vol.Optional(CONF_USE_SSL, default=DEFAULT_USE_SSL): bool,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Test the connection to the API."""
        session = async_get_clientsession(self.hass)
        client = ClaudeUsageApiClient(
            host=user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            api_key=user_input.get(CONF_API_KEY),
            use_ssl=user_input.get(CONF_USE_SSL, DEFAULT_USE_SSL),
            session=session,
        )

        # Test connection with health endpoint
        await client.async_get_health()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ClaudeUsageOptionsFlowHandler(config_entry)


class ClaudeUsageOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Claude Usage."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                }
            ),
        )
