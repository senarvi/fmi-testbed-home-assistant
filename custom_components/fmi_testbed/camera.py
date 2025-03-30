"""Camera platform for FMI Testbed radar integration."""

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable

import aiofiles
from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import SCAN_INTERVAL, TESTBED_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info=None,
):
    """Initializes the FMI Testbed camera platform.

    Args:
        hass: The Home Assistant instance.
        config: The configuration for the platform.
        async_add_entities: The function to add entities to the platform.
        discovery_info: Unused.
    """
    async_add_entities([FMITestbedCamera()])
    _LOGGER.info("Added the FMI Testbed radar camera")
    return True


class FMITestbedCamera(Camera):
    """FMI Testbed radar camera."""

    def __init__(self) -> None:
        super().__init__()
        self._cache_path = Path(tempfile.gettempdir()) / "fmi-testbed-cache.png"
        self._last_update = None

    @property
    def unique_id(self) -> str:
        """Returns a unique ID."""
        return "fmi_testbed"

    @property
    def name(self) -> str:
        """Returns the name of the camera."""
        return "FMI Testbed"

    @property
    def brand(self) -> str:
        """Returns the camera brand."""
        return "FMI"

    @property
    def model(self) -> str:
        """Returns the camera model."""
        return "Helsinki Testbed"

    @property
    def frame_interval(self) -> float:
        """Returns the interval between frames of the camera stream."""
        return SCAN_INTERVAL.total_seconds()

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Return the radar map image.

        Returns: The binary image.
        """

        try:
            await self._refresh_cache_if_invalid()
            if self._cache_path.is_file():
                async with aiofiles.open(self._cache_path, "rb") as file:
                    return await file.read()
        except Exception as e:
            _LOGGER.error(f"Error reading FMI Testbed radar image: {e}")
        return None

    async def _refresh_cache_if_invalid(self) -> None:
        """Updates the radar image cache if it doesn't exist or is too old."""

        if self._cache_path.is_file() and (self._last_update is not None):
            time_since_last_update = datetime.now() - self._last_update
            if time_since_last_update < SCAN_INTERVAL:
                _LOGGER.debug(
                    f"Cache exists and {time_since_last_update} since last update, "
                    f"which is less than {SCAN_INTERVAL}"
                )
                _LOGGER.debug("Not updating the cache yet")
                return

        image_urls = await self._read_image_urls()
        if not image_urls:
            _LOGGER.error("Failed to read image URLs from the animation page.")
            return

        await self._download_and_cache_image(image_urls[0])

    async def _read_image_urls(self) -> list[str]:
        """Update the camera image."""

        _LOGGER.debug(f"Reading the FMI Testbed animation page from {TESTBED_URL}")
        session = async_get_clientsession(self.hass)
        response = await session.get(TESTBED_URL)
        response_text = await response.text()
        if response.status != 200:
            _LOGGER.error(
                f"Could not download the FMI Testbed animation page: {response.status} - {response_text}"
            )
            return

        # Parse the HTML to extract the list of image URLs.
        pattern = r"var\s+anim_images_anim_anim\s+=\s+new\s+Array\s*\(([^)]*)\)"
        match = re.search(pattern, response_text, re.DOTALL)
        if not match:
            return []

        # Remove quotation from the URLs.
        return re.findall(r'["\'](.*?)["\']', match.group(1), re.DOTALL)

    async def _download_and_cache_image(self, url: str) -> None:
        """Downloads the image from the given URL and writes it to the cache path.

        Args:
            url: URL of the image to download.
        """

        _LOGGER.debug(f"Downloading the FMI Testbed radar image from {url}")
        session = async_get_clientsession(self.hass)
        response = await session.get(url)
        if response.status != 200:
            _LOGGER.error(
                f"Could not download the radar image: {response.status} - {await response.text()}"
            )
            return

        image_data = await response.read()
        async with aiofiles.open(self._cache_path, "wb") as file:
            await file.write(image_data)
        self._last_update = datetime.now()
        _LOGGER.debug("FMI Testbed radar image updated successfully")
