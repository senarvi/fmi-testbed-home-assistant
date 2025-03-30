"""Tests for the FMI Testbed camera platform."""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.fmi_testbed.camera import FMITestbedCamera
from custom_components.fmi_testbed.const import TESTBED_URL

TEST_HTML = """
<html>
<head><title>FMI Testbed</title></head>
<body>
<script>
var anim_images_anim_anim = new Array(
    "https://test.url/image1.png",
    "https://test.url/image2.png"
);
</script>
</body>
</html>
"""

IMAGE_URL = "https://test.url/image1.png"


async def mock_get(url):
    response = AsyncMock()
    response.status = 200
    if url == TESTBED_URL:
        response.text.return_value = TEST_HTML
    elif url == IMAGE_URL:
        response.read.return_value = b"mock-png"
    else:
        assert False, f"session.get() called with an unknown URL '{url}'."
    return response


@pytest.fixture
def session():
    result = MagicMock()
    result.get = mock_get
    return result


@pytest.fixture
def camera():
    """Fixture for creating a test camera instance."""
    with patch("tempfile.gettempdir", return_value="/tmp"):
        cam = FMITestbedCamera()
        cam.hass = MagicMock()
        cam.hass.async_add_executor_job = lambda f: f()
        yield cam
        # Cleanup
        if os.path.exists(cam._cache_path):
            os.remove(cam._cache_path)


@pytest.mark.asyncio
async def test_initial_properties(camera):
    """Test initial camera properties."""
    assert camera.unique_id == "fmi_testbed"
    assert camera.name == "FMI Testbed"


@pytest.mark.asyncio
async def test_async_camera_image_without_cache(camera, session):
    """Test updating the camera image when the cache doeosn't exist."""
    assert not os.path.exists(camera._cache_path)

    camera._last_update = datetime.now() - timedelta(minutes=1)
    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        image = await camera.async_camera_image()
    assert image == b"mock-png"

    camera._last_update = datetime.now() - timedelta(minutes=10)
    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        image = await camera.async_camera_image()
    assert image == b"mock-png"


@pytest.mark.asyncio
async def test_async_camera_image_with_cache(camera, session):
    """Test updating the camera image when the cache exists."""
    cached_image = b"mock-png-2"
    with open(camera._cache_path, "wb") as f:
        f.write(cached_image)

    camera._last_update = datetime.now() - timedelta(minutes=1)
    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        image = await camera.async_camera_image()
    assert image == cached_image

    camera._last_update = datetime.now() - timedelta(minutes=10)
    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        image = await camera.async_camera_image()
    assert image == b"mock-png"


@pytest.mark.asyncio
async def test_download_and_cache_success(camera, session):
    """Test image downloading and caching."""
    assert not os.path.exists(camera._cache_path)
    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        await camera._download_and_cache_image(IMAGE_URL)
        assert os.path.exists(camera._cache_path)
        with open(camera._cache_path, "rb") as f:
            assert f.read() == b"mock-png"


@pytest.mark.asyncio
async def test_download_and_cache_failure(camera):
    """Test failed image download."""
    mock_response = AsyncMock()
    mock_response.status = 404

    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=mock_response,
    ):
        await camera._download_and_cache_image(IMAGE_URL)
        assert not os.path.exists(camera._cache_path)


@pytest.mark.asyncio
async def test_read_image_urls(camera, session):
    """Test parsing image URLs from HTML."""
    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        urls = await camera._read_image_urls()
        assert len(urls) == 2
        assert urls[0] == "https://test.url/image1.png"
        assert urls[1] == "https://test.url/image2.png"


@pytest.mark.asyncio
async def test_read_image_urls_failure(camera):
    """Test handling of missing image URLs in HTML."""
    bad_html = "<html><body>No script here</body></html>"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = bad_html
    session = AsyncMock()
    session.get.return_value = mock_response

    with patch(
        "custom_components.fmi_testbed.camera.async_get_clientsession",
        return_value=session,
    ):
        urls = await camera._read_image_urls()
        assert not urls
