"""Tests for MiniDSPMediaPlayer entity."""

from __future__ import annotations

import importlib

import pytest
from homeassistant.const import STATE_OFF, STATE_ON

_mod = importlib.import_module("custom_components.minidsp-rs.media_player")
MiniDSPMediaPlayer = _mod.MiniDSPMediaPlayer

from .conftest import BASE_URL, MOCK_STATUS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _player(mock_coordinator) -> MiniDSPMediaPlayer:
    player = MiniDSPMediaPlayer(mock_coordinator)
    return player


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def test_state_on_when_connected(mock_coordinator):
    mock_coordinator.last_update_success = True
    player = _player(mock_coordinator)
    assert player.state == STATE_ON


def test_state_off_when_disconnected(mock_coordinator):
    mock_coordinator.last_update_success = False
    player = _player(mock_coordinator)
    assert player.state == STATE_OFF


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "db,expected_level",
    [
        (-127.0, 0.0),
        (0.0, 1.0),
        (-63.5, 0.5),
        (-20.0, pytest.approx(107 / 127, rel=1e-3)),
    ],
)
def test_volume_level_mapping(mock_coordinator, db, expected_level):
    mock_coordinator.data["master"]["volume"] = db
    player = _player(mock_coordinator)
    assert player.volume_level == expected_level


def test_volume_level_none_when_missing(mock_coordinator):
    mock_coordinator.data["master"].pop("volume", None)
    mock_coordinator.data = {"master": {}}
    player = _player(mock_coordinator)
    assert player.volume_level is None


def test_volume_level_clamped_below(mock_coordinator):
    """Values below -127 should clamp to 0.0."""
    mock_coordinator.data["master"]["volume"] = -200.0
    player = _player(mock_coordinator)
    assert player.volume_level == 0.0


def test_volume_level_clamped_above(mock_coordinator):
    """Values above 0 dB (unusual) should clamp to 1.0."""
    mock_coordinator.data["master"]["volume"] = 10.0
    player = _player(mock_coordinator)
    assert player.volume_level == 1.0


# ---------------------------------------------------------------------------
# Mute
# ---------------------------------------------------------------------------


def test_is_volume_muted_false(mock_coordinator):
    assert _player(mock_coordinator).is_volume_muted is False


def test_is_volume_muted_true(mock_coordinator):
    mock_coordinator.data["master"]["mute"] = True
    assert _player(mock_coordinator).is_volume_muted is True


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------


def test_source_mapped(mock_coordinator):
    mock_coordinator.data["master"]["source"] = "Analog"
    assert _player(mock_coordinator).source == "Analog"


def test_source_raw_passthrough_when_unmapped(mock_coordinator):
    mock_coordinator.data["master"]["source"] = "UnknownSource"
    assert _player(mock_coordinator).source == "UnknownSource"


def test_source_none_when_missing(mock_coordinator):
    mock_coordinator.data["master"].pop("source", None)
    mock_coordinator.data = {"master": {}}
    assert _player(mock_coordinator).source is None


def test_source_list_from_profile(mock_coordinator):
    player = _player(mock_coordinator)
    assert "Analog" in player.source_list
    assert "USB" in player.source_list


# ---------------------------------------------------------------------------
# Preset / sound mode
# ---------------------------------------------------------------------------


def test_sound_mode_preset_0(mock_coordinator):
    mock_coordinator.data["master"]["preset"] = 0
    assert _player(mock_coordinator).sound_mode == "Preset 1"


def test_sound_mode_preset_3(mock_coordinator):
    mock_coordinator.data["master"]["preset"] = 3
    assert _player(mock_coordinator).sound_mode == "Preset 4"


def test_sound_mode_none_when_missing(mock_coordinator):
    mock_coordinator.data = {"master": {}}
    assert _player(mock_coordinator).sound_mode is None


def test_sound_mode_list_length(mock_coordinator):
    player = _player(mock_coordinator)
    assert len(player.sound_mode_list) == 4
    assert "Preset 1" in player.sound_mode_list


# ---------------------------------------------------------------------------
# Extra state attributes
# ---------------------------------------------------------------------------


def test_extra_state_attributes_contains_dirac(mock_coordinator):
    attrs = _player(mock_coordinator).extra_state_attributes
    assert "dirac" in attrs
    assert attrs["dirac"] is True


# ---------------------------------------------------------------------------
# device_info
# ---------------------------------------------------------------------------


def test_device_info_from_coordinator(mock_coordinator):
    player = _player(mock_coordinator)
    assert player.device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# Service calls
# ---------------------------------------------------------------------------


async def test_set_volume_level(mock_coordinator):
    player = _player(mock_coordinator)
    await player.async_set_volume_level(0.5)
    mock_coordinator._api.async_set_volume.assert_awaited_once()
    called_gain = mock_coordinator._api.async_set_volume.call_args[0][0]
    assert abs(called_gain - (-63.5)) < 0.1
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_volume_up_clamps_at_one(mock_coordinator):
    mock_coordinator.data["master"]["volume"] = 0.0  # already at 1.0
    player = _player(mock_coordinator)
    await player.async_volume_up()
    mock_coordinator._api.async_set_volume.assert_awaited_once()
    gain = mock_coordinator._api.async_set_volume.call_args[0][0]
    assert gain <= 0.0  # never above 0 dB


async def test_volume_down_clamps_at_zero(mock_coordinator):
    mock_coordinator.data["master"]["volume"] = -127.0  # already at 0.0
    player = _player(mock_coordinator)
    await player.async_volume_down()
    gain = mock_coordinator._api.async_set_volume.call_args[0][0]
    assert gain >= -127.0


async def test_mute_volume(mock_coordinator):
    player = _player(mock_coordinator)
    await player.async_mute_volume(True)
    mock_coordinator._api.async_set_mute.assert_awaited_once_with(True)
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_select_source(mock_coordinator):
    player = _player(mock_coordinator)
    await player.async_select_source("USB")
    mock_coordinator._api.async_set_source.assert_awaited_once_with("Usb")
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_select_sound_mode_valid(mock_coordinator):
    player = _player(mock_coordinator)
    await player.async_select_sound_mode("Preset 2")
    mock_coordinator._api.async_set_preset.assert_awaited_once_with(1)
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_select_sound_mode_unknown_no_api_call(mock_coordinator):
    player = _player(mock_coordinator)
    await player.async_select_sound_mode("NonExistentPreset")
    mock_coordinator._api.async_set_preset.assert_not_called()
    mock_coordinator.async_request_refresh.assert_not_called()
