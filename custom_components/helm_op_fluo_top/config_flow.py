"""Config flow for Helm Op Fluo Top."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HoftAuthError, HoftClient, HoftConnectionError, PupilData
from .const import CONF_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

CODE_SCHEMA = vol.Schema({vol.Required(CONF_CODE): str})


class HoftConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a pupil by their Helm Op Fluo Top code."""

    VERSION = 1

    async def _async_validate(
        self, code: str, errors: dict[str, str]
    ) -> PupilData | None:
        client = HoftClient(async_get_clientsession(self.hass), code)
        try:
            return await client.async_get_pupil()
        except HoftAuthError:
            errors["base"] = "invalid_code"
        except HoftConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error while validating code")
            errors["base"] = "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            code = user_input[CONF_CODE].strip()
            pupil = await self._async_validate(code, errors)
            if pupil is not None:
                await self.async_set_unique_id(code.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=pupil.firstname or "Helm Op Fluo Top",
                    data={CONF_CODE: code},
                )

        return self.async_show_form(
            step_id="user", data_schema=CODE_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """The stored code stopped working (e.g. new school year)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            code = user_input[CONF_CODE].strip()
            pupil = await self._async_validate(code, errors)
            if pupil is not None:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    unique_id=code.lower(),
                    data_updates={CONF_CODE: code},
                )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=CODE_SCHEMA, errors=errors
        )
