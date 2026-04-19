"""Shared fixtures for minidsp-rs integration tests.

Note on imports: the custom component lives in custom_components/minidsp-rs/.
Because the directory name contains a hyphen, Python's normal import syntax
(`import custom_components.minidsp-rs`) is invalid. We work around this by:
  1. Using importlib.import_module("custom_components.minidsp-rs.<module>") to
     load modules as part of the package (preserving relative imports).
  2. The repo root must be on sys.path (pytest's default behaviour handles this).
"""

from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# HA version compatibility shims
# Installed HA may be older than the integration's 2024.8 requirement.
# Patch missing symbols so test collection does not fail in older envs.
# ---------------------------------------------------------------------------
import homeassistant.config_entries as _ce  # noqa: E402

if not hasattr(_ce, "ConfigFlowResult"):
    # ConfigFlowResult was added in HA 2024.4
    try:
        from homeassistant.data_entry_flow import FlowResult as _FR
        _ce.ConfigFlowResult = _FR  # type: ignore[attr-defined]
    except ImportError:
        _ce.ConfigFlowResult = dict  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:5380"

MOCK_STATUS: dict[str, Any] = {
    "master": {
        "volume": -20.0,
        "mute": False,
        "source": "Analog",
        "preset": 0,
        "dirac": True,
    },
    "input_levels": [-10, -12],
    "output_levels": [-15, -15, -20, -20],
    "outputs": [
        {"index": 0, "gain": 0.0},
        {"index": 1, "gain": 0.0},
        {"index": 2, "gain": -6.0},
        {"index": 3, "gain": -6.0},
    ],
}

MOCK_DEVICES: list[dict[str, Any]] = [
    {"product_name": "2x4 HD", "url": "http://localhost:5380"}
]


# ---------------------------------------------------------------------------
# Minimal hass fixture (no pytest-homeassistant-custom-component required)
# ---------------------------------------------------------------------------


class _MockHass:
    """Minimal HA instance stub sufficient for DataUpdateCoordinator + entities."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.bus = MagicMock()
        self.data: dict = {}
        self.config = MagicMock()
        self.config.config_dir = "/tmp"
        self.states = MagicMock()
        self.config_entries = MagicMock()
        self.config_entries._entries = {}
        # async_forward_entry_setups must be awaitable and return True
        self.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        # async_unload_platforms must return True
        self.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        # unique_id lookups return None (no existing entries)
        self.config_entries.async_entry_for_domain_unique_id = MagicMock(
            return_value=None
        )
        self.config_entries.async_entries = MagicMock(return_value=[])
        self.config_entries.async_update_entry = AsyncMock(return_value=None)

    def async_create_task(self, coro, *args, **kwargs):
        return self.loop.create_task(coro)


@pytest.fixture
def hass():
    return _MockHass()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_api():
    """Return a fully-mocked MiniDSPAPI instance.

    The ``async_subscribe_levels`` side-effect captures the callback so
    tests can invoke it directly via ``mock_api.captured_callback``.
    """
    api = MagicMock()
    api._base_url = BASE_URL

    # HTTP helpers
    api.async_get_status = AsyncMock(return_value=MOCK_STATUS)
    api.async_get_devices = AsyncMock(return_value=MOCK_DEVICES)
    api.async_post_config = AsyncMock(return_value=None)
    api.async_set_volume = AsyncMock(return_value=None)
    api.async_set_mute = AsyncMock(return_value=None)
    api.async_set_dirac = AsyncMock(return_value=None)
    api.async_set_source = AsyncMock(return_value=None)
    api.async_set_preset = AsyncMock(return_value=None)
    api.async_set_output_gain = AsyncMock(return_value=None)
    api.async_disconnect = AsyncMock(return_value=None)
    api.ws_connected = False
    api.last_ws_msg_at = None

    # WebSocket subscription — capture callback for later inspection
    _captured: list = []
    _unsubscribe = MagicMock()

    async def _subscribe(callback):
        _captured.clear()
        _captured.append(callback)
        return _unsubscribe

    api.async_subscribe_levels = AsyncMock(side_effect=_subscribe)
    api.captured_callback = _captured  # tests read _captured[0]
    api.unsubscribe_mock = _unsubscribe

    return api


@pytest.fixture
def mock_coordinator():
    """Return a lightweight MagicMock coordinator for entity unit tests.

    Avoids spinning up a real DataUpdateCoordinator / hass instance for
    pure property tests.
    """
    _const = importlib.import_module("custom_components.minidsp-rs.const")
    DEVICE_PROFILES = _const.DEVICE_PROFILES
    PROFILE_2X4HD = _const.PROFILE_2X4HD

    coord = MagicMock()
    coord.data = dict(MOCK_STATUS)
    coord.last_update_success = True
    coord.http_available = True
    coord.ws_available = True
    coord.last_http_ok = 123.0
    coord.last_ws_msg_at = 124.0
    coord.address = BASE_URL
    coord.name = "Test MiniDSP"
    coord.profile_name = PROFILE_2X4HD
    coord.profile = DEVICE_PROFILES[PROFILE_2X4HD]
    coord.device_info = {"product_name": "2x4 HD", "url": BASE_URL}
    coord.ha_device_info = {
        "identifiers": {("minidsp", BASE_URL)},
        "name": "Test MiniDSP",
        "manufacturer": "MiniDSP",
        "model": "2x4 HD",
    }
    coord._api = MagicMock()
    coord.api = coord._api
    coord._api.ws_connected = True
    coord._api.async_set_volume = AsyncMock()
    coord._api.async_set_mute = AsyncMock()
    coord._api.async_set_dirac = AsyncMock()
    coord._api.async_set_source = AsyncMock()
    coord._api.async_set_preset = AsyncMock()
    coord._api.async_set_output_gain = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


@pytest.fixture
async def real_coordinator(hass, mock_api):
    """Return a real MiniDSPCoordinator wired to a mock API and hass."""
    _const = importlib.import_module("custom_components.minidsp-rs.const")
    DEVICE_PROFILES = _const.DEVICE_PROFILES
    PROFILE_2X4HD = _const.PROFILE_2X4HD
    _cm = importlib.import_module("custom_components.minidsp-rs.coordinator")
    MiniDSPCoordinator = _cm.MiniDSPCoordinator

    profile = DEVICE_PROFILES[PROFILE_2X4HD]
    coord = MiniDSPCoordinator(
        hass=hass,
        api=mock_api,
        name="Test MiniDSP",
        profile=profile,
        profile_name=PROFILE_2X4HD,
    )
    coord.device_info = {"product_name": "2x4 HD", "url": BASE_URL}
    coord.async_set_updated_data(dict(MOCK_STATUS))
    return coord
