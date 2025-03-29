"""FMI Testbed radar integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the FMI Radar component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up FMI Radar from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "camera")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "camera")
