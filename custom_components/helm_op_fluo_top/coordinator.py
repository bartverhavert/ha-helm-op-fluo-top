"""Data update coordinator for Helm Op Fluo Top."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HoftAuthError, HoftClient, HoftConnectionError, PupilData
from .const import CONF_CODE, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type HoftConfigEntry = ConfigEntry[HoftCoordinator]


class HoftCoordinator(DataUpdateCoordinator[PupilData]):
    """Polls the API for one pupil."""

    config_entry: HoftConfigEntry

    def __init__(self, hass: HomeAssistant, entry: HoftConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = HoftClient(async_get_clientsession(hass), entry.data[CONF_CODE])

    async def _async_update_data(self) -> PupilData:
        try:
            return await self.client.async_get_pupil()
        except HoftAuthError as err:
            # Triggers the reauth flow, e.g. when a new school year issues new codes.
            raise ConfigEntryAuthFailed(str(err)) from err
        except HoftConnectionError as err:
            raise UpdateFailed(str(err)) from err
