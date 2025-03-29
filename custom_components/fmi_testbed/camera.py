"""Camera platform for FMI Testbed radar integration."""

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable

from bs4 import BeautifulSoup
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
    _LOGGER.info("Added FMI Testbed radar camera")
    return True


class FMITestbedCamera(Camera):
    """FMI Testbed radar camera."""

    def __init__(self):
        super().__init__()
        self._cache_path = Path(tempfile.gettempdir()) / "fmi-testbed-cache.png"
        self._last_update = None

    @property
    def unique_id(self) -> str:
        """Returns a unique ID."""
        return "fmi_testbed"

    @property
    def name(self):
        """Returns the name of the camera."""
        return "FMI Testbed"

    async def async_camera_image(self) -> bytes | None:
        """Return bytes of camera image."""
        await self._update_image()
        if self._cache_path.is_file():
            with open(self._cache_path, "rb") as file:
                return file.read()
        return None

    async def _update_image(self):
        """Update the camera image."""
        if self._cache_path.is_file() and (self._last_update is not None):
            time_since_last_update = datetime.now() - self._last_update
            if time_since_last_update < SCAN_INTERVAL:
                _LOGGER.debug(
                    f"{time_since_last_update} since last update, which is less than {SCAN_INTERVAL}. Not updating the radar image yet"
                )
                return

        try:
            session = async_get_clientsession(self.hass)
            response = await session.get(TESTBED_URL)
            text = await response.text()

            # Parse HTML to extract latest image URL
            soup = BeautifulSoup(text, "html.parser")
            script_tag = soup.find(
                "script", text=lambda t: "anim_images_anim_anim" in str(t)
            )
            if not script_tag:
                _LOGGER.error(
                    "Animation script was not found from the FMI Testbed HTML page"
                )
                return

            pattern = r"var\s+anim_images_anim_anim\s+=\s+new\s+Array\s*\(([^)]*)\)"
            match = re.search(pattern, script_tag.string, re.DOTALL)
            if not match:
                _LOGGER.error(
                    "Could not parse the image URLs from the animation JavaScript"
                )
                return

            urls = re.findall(r'["\'](.*?)["\']', match.group(1), re.DOTALL)
            if not urls:
                _LOGGER.error("Could not parse the image URLs from JavaScript array")
                return

            await self._download_and_cache_image(urls[0])
        except Exception as e:
            _LOGGER.error(f"Error updating FMI Testbed radar image: {e}")

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
        with open(self._cache_path, "wb") as file:
            file.write(image_data)
        self._last_update = datetime.now()
        _LOGGER.debug("FMI Testbed radar image updated successfully")
