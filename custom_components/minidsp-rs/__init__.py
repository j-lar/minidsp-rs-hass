from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MiniDSPAPI
from .const import (
    CONF_DEVICE_INDEX,
    CONF_MODEL,
    DEVICE_PROFILES,
    DOMAIN,
    PRODUCT_NAME_MODEL_MAP,
    PROFILE_2X4HD,
    PROFILE_GENERIC,
    validate_profile,
)
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    "media_player",
    "sensor",
    "binary_sensor",
    "switch",
    "number",
    "select",
]


async def async_setup(hass: HomeAssistant, config: dict):  # type: ignore[arg-type]
    """YAML setup not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MiniDSP from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Ensure we reload when options change
    entry.async_on_unload(entry.add_update_listener(_update_listener))

    base_url: str | None = entry.options.get(CONF_URL) if entry.options else None
    if not base_url:
        base_url = entry.data.get(CONF_URL)
    if not base_url:
        _LOGGER.error("Config entry missing base URL")
        raise ConfigEntryNotReady

    session = async_get_clientsession(hass)
    device_index = int(
        entry.options.get(CONF_DEVICE_INDEX, entry.data.get(CONF_DEVICE_INDEX, 0))
    )
    api = MiniDSPAPI(base_url, session, device_index=device_index)
    model = entry.options.get(CONF_MODEL) or entry.data.get(CONF_MODEL)
    device_info = None
    model_from_device = None
    if not model:
        try:
            devices = await api.async_get_devices()
            if devices:
                device_info = (
                    devices[device_index]
                    if 0 <= device_index < len(devices)
                    else devices[0]
                )
                product_name = str(device_info.get("product_name", "")).lower()
                model_from_device = PRODUCT_NAME_MODEL_MAP.get(product_name)
                if model_from_device is None and product_name:
                    for key, value in PRODUCT_NAME_MODEL_MAP.items():
                        if key in product_name:
                            model_from_device = value
                            break
                model = model_from_device or PROFILE_GENERIC
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to auto-detect device model: %s", err)
    if not model:
        model = PROFILE_2X4HD
    if device_info is None:
        try:
            devices = await api.async_get_devices()
            if devices:
                device_info = (
                    devices[device_index]
                    if 0 <= device_index < len(devices)
                    else devices[0]
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to fetch device info: %s", err)
    profile = DEVICE_PROFILES.get(model, DEVICE_PROFILES[PROFILE_2X4HD])
    if not validate_profile(profile):
        _LOGGER.warning(
            "Invalid device profile %s, falling back to %s",
            model,
            PROFILE_2X4HD,
        )
        model = PROFILE_2X4HD
        profile = DEVICE_PROFILES[PROFILE_2X4HD]
    coordinator = MiniDSPCoordinator(
        hass, api, name=entry.title, profile=profile, profile_name=model
    )
    coordinator.device_info = device_info
    if model_from_device and entry.options.get(CONF_MODEL) != model_from_device:
        hass.async_create_task(
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, CONF_MODEL: model_from_device}
            )
        )

    try:
        await coordinator.async_config_entry_first_refresh()
        await coordinator.async_start()
    except Exception as err:
        raise ConfigEntryNotReady from err

    # Store
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Forward media_player first to make it appear first in UI entity list
    await hass.config_entries.async_forward_entry_setups(entry, ["media_player"])
    # Forward remaining platforms
    await hass.config_entries.async_forward_entry_setups(
        entry, [p for p in PLATFORMS if p != "media_player"]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        stored = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if stored and "coordinator" in stored:
            coordinator: MiniDSPCoordinator = stored["coordinator"]
            await coordinator.async_disconnect()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry (triggered by HA)."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options/config flow updates by reloading the integration."""
    await hass.config_entries.async_reload(entry.entry_id)
