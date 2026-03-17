from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import MiniDSPAPI
from .const import (
    CONF_DEVICE_INDEX,
    CONF_DIRAC_UPGRADE,
    CONF_LEVEL_INTERVAL,
    CONF_MODEL,
    DEFAULT_LEVEL_INTERVAL,
    DEVICE_PROFILES,
    DOMAIN,
    PROFILE_2X4HD,
)

from homeassistant import config_entries

_LOGGER = logging.getLogger(__name__)


class MiniDSPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the MiniDSP integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where the user enters the base URL."""

        errors = {}

        if user_input is not None:
            base_url = user_input[CONF_URL]
            title = user_input.get(CONF_NAME, base_url)
            model = user_input.get(CONF_MODEL, PROFILE_2X4HD)
            device_index = int(user_input.get(CONF_DEVICE_INDEX, 0))

            if not await self._async_validate_url(base_url):
                errors["base"] = "cannot_connect"
            else:
                # Use base_url as unique_id to prevent duplicates
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_URL: base_url,
                        CONF_MODEL: model,
                        CONF_DEVICE_INDEX: device_index,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
                vol.Optional(CONF_NAME): str,
                vol.Required(CONF_DEVICE_INDEX, default=0): vol.Coerce(int),
                vol.Required(CONF_MODEL, default=PROFILE_2X4HD): vol.In(
                    list(DEVICE_PROFILES.keys())
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _async_validate_url(self, base_url: str) -> bool:
        """Test connectivity to the minidsp-rs daemon."""
        session = async_get_clientsession(self.hass)
        api = MiniDSPAPI(base_url, session)
        try:
            await api.async_get_devices()
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Failed to reach MiniDSP at %s", base_url)
            return False
        return True

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MiniDSPOptionsFlow:
        """Return the options flow handler."""
        return MiniDSPOptionsFlow(config_entry)


class MiniDSPOptionsFlow(config_entries.OptionsFlow):
    """Handle options for an existing config entry."""

    def __init__(self, entry: config_entries.ConfigEntry):
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):  # type: ignore[override]
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_URL: user_input[CONF_URL],
                    CONF_MODEL: user_input.get(CONF_MODEL, PROFILE_2X4HD),
                    CONF_DEVICE_INDEX: int(user_input.get(CONF_DEVICE_INDEX, 0)),
                    CONF_LEVEL_INTERVAL: float(
                        user_input.get(CONF_LEVEL_INTERVAL, DEFAULT_LEVEL_INTERVAL)
                    ),
                    CONF_DIRAC_UPGRADE: bool(
                        user_input.get(CONF_DIRAC_UPGRADE, False)
                    ),
                },
            )

        current_url = self._entry.options.get(
            CONF_URL, self._entry.data.get(CONF_URL, "")
        )
        current_model = self._entry.options.get(
            CONF_MODEL, self._entry.data.get(CONF_MODEL, PROFILE_2X4HD)
        )
        current_device_index = self._entry.options.get(
            CONF_DEVICE_INDEX, self._entry.data.get(CONF_DEVICE_INDEX, 0)
        )
        current_level_interval = float(
            self._entry.options.get(
                CONF_LEVEL_INTERVAL,
                self._entry.data.get(CONF_LEVEL_INTERVAL, DEFAULT_LEVEL_INTERVAL),
            )
        )
        current_profile = DEVICE_PROFILES.get(current_model, {})
        dirac_is_upgrade = current_profile.get("dirac_is_upgrade", False)
        current_dirac_upgrade = bool(
            self._entry.options.get(
                CONF_DIRAC_UPGRADE,
                self._entry.data.get(CONF_DIRAC_UPGRADE, False),
            )
        )

        fields: dict = {
            vol.Required(CONF_URL, default=current_url): str,
            vol.Required(CONF_DEVICE_INDEX, default=current_device_index): vol.Coerce(int),
            vol.Required(CONF_MODEL, default=current_model): vol.In(
                list(DEVICE_PROFILES.keys())
            ),
            vol.Required(
                CONF_LEVEL_INTERVAL, default=current_level_interval
            ): vol.In([0.0, 0.25, 0.5, 1.0, 2.0, 5.0]),
        }
        if dirac_is_upgrade:
            fields[vol.Optional(CONF_DIRAC_UPGRADE, default=current_dirac_upgrade)] = bool

        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
