"""Tests for DiracLiveSwitch and MuteSwitch entities."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("custom_components.minidsp-rs.switch")
DiracLiveSwitch = _mod.DiracLiveSwitch
MuteSwitch = _mod.MuteSwitch


# ---------------------------------------------------------------------------
# DiracLiveSwitch
# ---------------------------------------------------------------------------


def test_dirac_is_on_true(mock_coordinator):
    mock_coordinator.data["master"]["dirac"] = True
    switch = DiracLiveSwitch(mock_coordinator)
    assert switch.is_on is True


def test_dirac_is_on_false(mock_coordinator):
    mock_coordinator.data["master"]["dirac"] = False
    switch = DiracLiveSwitch(mock_coordinator)
    assert switch.is_on is False


async def test_dirac_turn_on(mock_coordinator):
    switch = DiracLiveSwitch(mock_coordinator)
    await switch.async_turn_on()
    mock_coordinator._api.async_set_dirac.assert_awaited_once_with(True)
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_dirac_turn_off(mock_coordinator):
    switch = DiracLiveSwitch(mock_coordinator)
    await switch.async_turn_off()
    mock_coordinator._api.async_set_dirac.assert_awaited_once_with(False)
    mock_coordinator.async_request_refresh.assert_awaited_once()


def test_dirac_device_info_from_coordinator(mock_coordinator):
    assert DiracLiveSwitch(mock_coordinator).device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# MuteSwitch
# ---------------------------------------------------------------------------


def test_mute_is_on_false(mock_coordinator):
    mock_coordinator.data["master"]["mute"] = False
    assert MuteSwitch(mock_coordinator).is_on is False


def test_mute_is_on_true(mock_coordinator):
    mock_coordinator.data["master"]["mute"] = True
    assert MuteSwitch(mock_coordinator).is_on is True


async def test_mute_turn_on(mock_coordinator):
    switch = MuteSwitch(mock_coordinator)
    await switch.async_turn_on()
    mock_coordinator._api.async_set_mute.assert_awaited_once_with(True)
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_mute_turn_off(mock_coordinator):
    switch = MuteSwitch(mock_coordinator)
    await switch.async_turn_off()
    mock_coordinator._api.async_set_mute.assert_awaited_once_with(False)
    mock_coordinator.async_request_refresh.assert_awaited_once()


def test_mute_device_info_from_coordinator(mock_coordinator):
    assert MuteSwitch(mock_coordinator).device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# kwargs accepted (SwitchEntity interface compatibility)
# ---------------------------------------------------------------------------


async def test_dirac_turn_on_accepts_kwargs(mock_coordinator):
    switch = DiracLiveSwitch(mock_coordinator)
    await switch.async_turn_on(extra="ignored")  # must not raise


async def test_mute_turn_off_accepts_kwargs(mock_coordinator):
    switch = MuteSwitch(mock_coordinator)
    await switch.async_turn_off(extra="ignored")  # must not raise
