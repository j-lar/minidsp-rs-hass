"""Tests for PresetSelect and SourceSelect entities.

Note: our integration module is named 'select.py', which shadows Python's
built-in 'select' module. We import it explicitly via importlib.
"""

from __future__ import annotations

import importlib
import sys

# Load our select module by file path to avoid shadowing the built-in
_sel = importlib.import_module("custom_components.minidsp-rs.select")
PresetSelect = _sel.PresetSelect
SourceSelect = _sel.SourceSelect


# ---------------------------------------------------------------------------
# PresetSelect
# ---------------------------------------------------------------------------


def test_preset_current_option_preset_0(mock_coordinator):
    mock_coordinator.data["master"]["preset"] = 0
    assert PresetSelect(mock_coordinator).current_option == "Preset 1"


def test_preset_current_option_preset_3(mock_coordinator):
    mock_coordinator.data["master"]["preset"] = 3
    assert PresetSelect(mock_coordinator).current_option == "Preset 4"


def test_preset_current_option_none_when_missing(mock_coordinator):
    mock_coordinator.data = {"master": {}}
    assert PresetSelect(mock_coordinator).current_option is None


def test_preset_options_length(mock_coordinator):
    options = PresetSelect(mock_coordinator).options
    assert len(options) == 4
    assert "Preset 1" in options
    assert "Preset 4" in options


async def test_preset_select_valid(mock_coordinator):
    entity = PresetSelect(mock_coordinator)
    await entity.async_select_option("Preset 2")
    mock_coordinator._api.async_set_preset.assert_awaited_once_with(1)
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_preset_select_first(mock_coordinator):
    entity = PresetSelect(mock_coordinator)
    await entity.async_select_option("Preset 1")
    mock_coordinator._api.async_set_preset.assert_awaited_once_with(0)


async def test_preset_select_invalid_no_api_call(mock_coordinator):
    entity = PresetSelect(mock_coordinator)
    await entity.async_select_option("InvalidPreset")
    mock_coordinator._api.async_set_preset.assert_not_called()
    mock_coordinator.async_request_refresh.assert_not_called()


def test_preset_device_info_from_coordinator(mock_coordinator):
    assert PresetSelect(mock_coordinator).device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# SourceSelect
# ---------------------------------------------------------------------------


def test_source_current_option_analog(mock_coordinator):
    mock_coordinator.data["master"]["source"] = "Analog"
    assert SourceSelect(mock_coordinator).current_option == "Analog"


def test_source_current_option_usb(mock_coordinator):
    mock_coordinator.data["master"]["source"] = "Usb"
    # 2x4HD profile maps "Usb" → "USB"
    assert SourceSelect(mock_coordinator).current_option == "USB"


def test_source_current_option_raw_passthrough(mock_coordinator):
    """Unmapped API values pass through as-is."""
    mock_coordinator.data["master"]["source"] = "SomeUnknownSource"
    assert SourceSelect(mock_coordinator).current_option == "SomeUnknownSource"


def test_source_current_option_none_when_missing(mock_coordinator):
    mock_coordinator.data = {"master": {}}
    assert SourceSelect(mock_coordinator).current_option is None


def test_source_options_from_profile(mock_coordinator):
    options = SourceSelect(mock_coordinator).options
    assert "Analog" in options
    assert "USB" in options
    assert "TOSLINK" in options


async def test_source_select_option(mock_coordinator):
    entity = SourceSelect(mock_coordinator)
    await entity.async_select_option("USB")
    mock_coordinator._api.async_set_source.assert_awaited_once_with("Usb")
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_source_select_toslink(mock_coordinator):
    entity = SourceSelect(mock_coordinator)
    await entity.async_select_option("TOSLINK")
    mock_coordinator._api.async_set_source.assert_awaited_once_with("Toslink")


def test_source_device_info_from_coordinator(mock_coordinator):
    assert SourceSelect(mock_coordinator).device_info == mock_coordinator.ha_device_info
