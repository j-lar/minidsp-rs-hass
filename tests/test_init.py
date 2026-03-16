"""Tests for integration setup and teardown (__init__.py)."""

from __future__ import annotations

import importlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_URL
from homeassistant.exceptions import ConfigEntryNotReady

from .conftest import BASE_URL, MOCK_DEVICES, MOCK_STATUS

_const_mod = importlib.import_module("custom_components.minidsp-rs.const")
CONF_MODEL = _const_mod.CONF_MODEL
DOMAIN = _const_mod.DOMAIN
PROFILE_2X4HD = _const_mod.PROFILE_2X4HD


# ---------------------------------------------------------------------------
# Minimal ConfigEntry stub
# ---------------------------------------------------------------------------


class _MockEntry:
    def __init__(self, data=None, options=None, title="test"):
        self.entry_id = str(uuid.uuid4())
        self.data = data or {}
        self.options = options or {}
        self.title = title
        self._listeners = []

    def add_to_hass(self, hass):
        hass.data.setdefault(DOMAIN, {})

    def async_on_unload(self, func):
        self._listeners.append(func)
        return lambda: None

    def add_update_listener(self, func):
        self._listeners.append(func)
        return lambda: None


def _entry(**kwargs):
    defaults = {
        "data": {CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD},
        "options": {},
    }
    defaults.update(kwargs)
    return _MockEntry(**defaults)


def _load_init():
    return importlib.import_module("custom_components.minidsp-rs")


@pytest.fixture
def init_mod():
    return _load_init()


@pytest.fixture
def patched_api(init_mod, mock_api):
    with patch.object(init_mod, "MiniDSPAPI", return_value=mock_api):
        yield mock_api


# ---------------------------------------------------------------------------
# async_setup_entry
# ---------------------------------------------------------------------------


async def test_setup_entry_success(hass, init_mod, patched_api):
    entry = _entry()
    result = await init_mod.async_setup_entry(hass, entry)
    assert result is True
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]
    stored = hass.data[DOMAIN][entry.entry_id]
    assert "coordinator" in stored
    assert "api" in stored


async def test_setup_entry_stores_coordinator(hass, init_mod, patched_api):
    _coord_mod = importlib.import_module("custom_components.minidsp-rs.coordinator")
    entry = _entry()
    await init_mod.async_setup_entry(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert isinstance(coordinator, _coord_mod.MiniDSPCoordinator)


async def test_setup_entry_missing_url_raises(hass, init_mod):
    entry = _entry(data={}, options={})
    with pytest.raises(ConfigEntryNotReady):
        await init_mod.async_setup_entry(hass, entry)


async def test_setup_entry_api_failure_raises(hass, init_mod, mock_api):
    mock_api.async_get_status = AsyncMock(side_effect=Exception("connection refused"))
    with patch.object(init_mod, "MiniDSPAPI", return_value=mock_api):
        entry = _entry()
        with pytest.raises(ConfigEntryNotReady):
            await init_mod.async_setup_entry(hass, entry)


async def test_setup_entry_uses_options_url_over_data(hass, init_mod, mock_api):
    options_url = "http://192.168.1.99:5380"
    entry = _entry(options={CONF_URL: options_url, CONF_MODEL: PROFILE_2X4HD})

    with patch.object(init_mod, "MiniDSPAPI", return_value=mock_api) as mock_cls:
        await init_mod.async_setup_entry(hass, entry)
        assert mock_cls.call_args[0][0] == options_url


async def test_setup_entry_autodetects_model(hass, init_mod, mock_api):
    entry = _entry(data={CONF_URL: BASE_URL}, options={})
    mock_api.async_get_devices = AsyncMock(return_value=MOCK_DEVICES)

    with patch.object(init_mod, "MiniDSPAPI", return_value=mock_api):
        await init_mod.async_setup_entry(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert coordinator.profile_name == PROFILE_2X4HD


# ---------------------------------------------------------------------------
# async_unload_entry
# ---------------------------------------------------------------------------


async def test_unload_entry(hass, init_mod, patched_api):
    entry = _entry()
    await init_mod.async_setup_entry(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    with patch.object(coordinator, "async_disconnect", new=AsyncMock()) as mock_disc:
        with patch.object(init_mod, "PLATFORMS", []):  # skip platform unload
            result = await init_mod.async_unload_entry(hass, entry)
    assert result is True
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    mock_disc.assert_awaited_once()
