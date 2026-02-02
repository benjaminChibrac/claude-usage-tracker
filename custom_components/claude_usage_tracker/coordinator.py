"""Data update coordinator for Claude Usage integration."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ClaudeUsageApiClient, ClaudeUsageApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ClaudeUsageDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Claude usage data."""

    def __init__(
        self, hass: HomeAssistant, client: ClaudeUsageApiClient, scan_interval: int
    ):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            return await self.client.async_get_usage()
        except ClaudeUsageApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
