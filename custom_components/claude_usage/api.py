"""API client for Claude Usage Tracker."""
import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class ClaudeUsageApiError(Exception):
    """Base exception for API errors."""


class ClaudeUsageAuthError(ClaudeUsageApiError):
    """Exception for authentication errors."""


class ClaudeUsageConnectionError(ClaudeUsageApiError):
    """Exception for connection errors."""


class ClaudeUsageApiClient:
    """API client for Claude Usage Tracker."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str | None = None,
        use_ssl: bool = False,
        session: aiohttp.ClientSession | None = None,
    ):
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.api_key = api_key
        self.use_ssl = use_ssl
        self._session = session
        self._close_session = False

        protocol = "https" if use_ssl else "http"
        self.base_url = f"{protocol}://{host}:{port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True
        return self._session

    async def close(self):
        """Close the aiohttp session if we created it."""
        if self._close_session and self._session:
            await self._session.close()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def async_get_usage(self) -> dict[str, Any]:
        """Get usage data from API."""
        session = await self._get_session()
        url = f"{self.base_url}/usage"

        try:
            async with asyncio.timeout(30):
                async with session.get(
                    url, headers=self._get_headers()
                ) as response:
                    if response.status == 401:
                        raise ClaudeUsageAuthError("Invalid API key")
                    if response.status != 200:
                        text = await response.text()
                        raise ClaudeUsageApiError(
                            f"API returned status {response.status}: {text}"
                        )
                    return await response.json()
        except aiohttp.ClientError as err:
            raise ClaudeUsageConnectionError(f"Connection error: {err}") from err
        except Exception as err:
            raise ClaudeUsageApiError(f"Unexpected error: {err}") from err

    async def async_get_health(self) -> dict[str, Any]:
        """Get health status from API."""
        session = await self._get_session()
        url = f"{self.base_url}/health"

        try:
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise ClaudeUsageApiError(
                            f"Health check failed with status {response.status}: {text}"
                        )
                    return await response.json()
        except aiohttp.ClientError as err:
            raise ClaudeUsageConnectionError(f"Connection error: {err}") from err
        except Exception as err:
            raise ClaudeUsageApiError(f"Unexpected error: {err}") from err
