"""Tests for MiniDSPOutputGain number entities."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock

_mod = importlib.import_module("custom_components.minidsp-rs.number")
MiniDSPOutputGain = _mod.MiniDSPOutputGain

from .conftest import MOCK_STATUS


# ---------------------------------------------------------------------------
# native_value
# ---------------------------------------------------------------------------


def test_native_value_output_0(mock_coordinator):
    entity = MiniDSPOutputGain(mock_coordinator, 0)
    assert entity.native_value == 0.0


def test_native_value_output_2(mock_coordinator):
    entity = MiniDSPOutputGain(mock_coordinator, 2)
    assert entity.native_value == -6.0


def test_native_value_not_found_returns_none(mock_coordinator):
    entity = MiniDSPOutputGain(mock_coordinator, 99)
    assert entity.native_value is None


def test_native_value_missing_outputs_returns_none(mock_coordinator):
    mock_coordinator.data = {}
    entity = MiniDSPOutputGain(mock_coordinator, 0)
    assert entity.native_value is None


# ---------------------------------------------------------------------------
# Entity naming — 1-indexed
# ---------------------------------------------------------------------------


def test_entity_name_is_1indexed():
    _const = importlib.import_module("custom_components.minidsp-rs.const")
    DEVICE_PROFILES = _const.DEVICE_PROFILES
    PROFILE_2X4HD = _const.PROFILE_2X4HD

    coord = MagicMock()
    coord.address = "http://localhost:5380"
    coord.profile = DEVICE_PROFILES[PROFILE_2X4HD]

    e0 = MiniDSPOutputGain(coord, 0)
    assert e0._attr_name == "Output 1 Gain"

    e3 = MiniDSPOutputGain(coord, 3)
    assert e3._attr_name == "Output 4 Gain"


# ---------------------------------------------------------------------------
# async_set_native_value
# ---------------------------------------------------------------------------


async def test_set_native_value(mock_coordinator):
    entity = MiniDSPOutputGain(mock_coordinator, 1)
    await entity.async_set_native_value(-3.0)
    mock_coordinator._api.async_set_output_gain.assert_awaited_once_with(1, -3.0)
    mock_coordinator.async_request_refresh.assert_awaited_once()


# ---------------------------------------------------------------------------
# device_info
# ---------------------------------------------------------------------------


def test_device_info_from_coordinator(mock_coordinator):
    entity = MiniDSPOutputGain(mock_coordinator, 0)
    assert entity.device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# async_setup_entry creates one entity per output channel
# ---------------------------------------------------------------------------


async def test_setup_entry_creates_entities(hass, real_coordinator):
    _number_mod = importlib.import_module("custom_components.minidsp-rs.number")
    async_setup_entry = _number_mod.async_setup_entry
    _const = importlib.import_module("custom_components.minidsp-rs.const")
    DOMAIN = _const.DOMAIN
    from homeassistant.config_entries import ConfigEntry

    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": real_coordinator
    }

    added = []
    await async_setup_entry(hass, entry, lambda entities, **kw: added.extend(entities))

    # MOCK_STATUS has 4 output_levels
    assert len(added) == 4
    assert all(isinstance(e, MiniDSPOutputGain) for e in added)
