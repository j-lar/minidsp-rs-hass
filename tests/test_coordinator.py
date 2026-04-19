"""Tests for MiniDSPCoordinator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import importlib

import pytest

_coord_mod = importlib.import_module("custom_components.minidsp-rs.coordinator")
MiniDSPCoordinator = _coord_mod.MiniDSPCoordinator

_const_mod = importlib.import_module("custom_components.minidsp-rs.const")
DEVICE_PROFILES = _const_mod.DEVICE_PROFILES
DOMAIN = _const_mod.DOMAIN
HEALTH_POLL_INTERVAL_SECONDS = _const_mod.HEALTH_POLL_INTERVAL_SECONDS
PROFILE_2X4HD = _const_mod.PROFILE_2X4HD

from .conftest import BASE_URL, MOCK_STATUS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_coordinator(hass, mock_api, *, profile_name=PROFILE_2X4HD, device_info=None):
    profile = DEVICE_PROFILES[profile_name]
    coord = MiniDSPCoordinator(
        hass=hass,
        api=mock_api,
        name="Test MiniDSP",
        profile=profile,
        profile_name=profile_name,
    )
    coord.device_info = device_info
    return coord


# ---------------------------------------------------------------------------
# _async_update_data
# ---------------------------------------------------------------------------


async def test_update_data_returns_rounded(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    # mock_api.async_get_status returns MOCK_STATUS (volume -20.0)
    data = await coord._async_update_data()
    assert data["master"]["volume"] == -20  # rounded
    assert isinstance(data["input_levels"][0], int)
    assert coord.http_available is True
    assert coord.last_http_ok is not None


async def test_update_data_raises_update_failed_on_error(hass, mock_api):
    from homeassistant.helpers.update_coordinator import UpdateFailed

    mock_api.async_get_status = AsyncMock(side_effect=RuntimeError("unreachable"))
    coord = _make_coordinator(hass, mock_api)
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
    assert coord.http_available is False


async def test_periodic_http_recovery_path(hass, mock_api):
    from homeassistant.helpers.update_coordinator import UpdateFailed

    coord = _make_coordinator(hass, mock_api)
    mock_api.async_get_status = AsyncMock(side_effect=RuntimeError("down"))
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
    assert coord.http_available is False

    mock_api.async_get_status = AsyncMock(return_value=MOCK_STATUS)
    data = await coord._async_update_data()
    assert data["master"]["volume"] == -20
    assert coord.http_available is True
    assert coord.transport_available is True


# ---------------------------------------------------------------------------
# _rounded_levels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (
            {"levels": [-10.3, -9.7], "gain": 1.2},
            {"levels": [-10, -10], "gain": 1},
        ),
        (
            # Python uses banker's rounding: round(-20.5) == -20 (rounds to even)
            {"master": {"volume": -20.5, "source": "Analog"}},
            {"master": {"volume": -20, "source": "Analog"}},
        ),
        ({"non_numeric": "hello"}, {"non_numeric": "hello"}),
    ],
)
def test_rounded_levels(hass, mock_api, input_data, expected):
    coord = _make_coordinator(hass, mock_api)
    result = coord._rounded_levels(input_data)
    assert result == expected


# ---------------------------------------------------------------------------
# ha_device_info
# ---------------------------------------------------------------------------


def test_ha_device_info_with_product_name(hass, mock_api):
    coord = _make_coordinator(
        hass, mock_api, device_info={"product_name": "2x4 HD", "url": BASE_URL}
    )
    info = coord.ha_device_info
    assert info["manufacturer"] == "MiniDSP"
    assert info["model"] == "2x4 HD"
    assert (DOMAIN, BASE_URL) in info["identifiers"]


def test_ha_device_info_falls_back_to_profile(hass, mock_api):
    coord = _make_coordinator(hass, mock_api, device_info=None)
    info = coord.ha_device_info
    assert info["model"] == PROFILE_2X4HD


# ---------------------------------------------------------------------------
# _levels_callback (accessed via async_start + captured callback)
# ---------------------------------------------------------------------------


async def _get_callback(coord: MiniDSPCoordinator, mock_api) -> Any:
    """Start the coordinator and return the captured WebSocket callback."""
    await coord.async_start()
    assert mock_api.captured_callback, "callback not captured — subscribe not called"
    return mock_api.captured_callback[0]


async def test_levels_callback_reconnect_triggers_refresh(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    coord.async_set_updated_data(dict(MOCK_STATUS))
    cb = await _get_callback(coord, mock_api)

    with patch.object(coord, "async_request_refresh", new=AsyncMock()) as mock_refresh:
        # Simulate the reconnect event dispatched by api.py
        with patch.object(coord.hass, "async_create_task") as mock_task:
            await cb({"_reconnected": True})
            mock_task.assert_called_once()


async def test_levels_callback_updates_input_levels(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    coord.async_set_updated_data(dict(MOCK_STATUS))
    cb = await _get_callback(coord, mock_api)

    new_levels = [-5, -6]
    with patch.object(coord, "async_set_updated_data", Mock()) as mock_set:
        await cb({"input_levels": new_levels})
        mock_set.assert_called_once()
        updated = mock_set.call_args[0][0]
        assert updated["input_levels"] == new_levels
        assert coord.last_ws_msg_at is not None


async def test_levels_callback_no_op_when_unchanged(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    coord.async_set_updated_data(dict(MOCK_STATUS))
    cb = await _get_callback(coord, mock_api)

    with patch.object(coord, "async_set_updated_data", Mock()) as mock_set:
        # Send same levels as MOCK_STATUS — should not trigger update
        await cb({"input_levels": MOCK_STATUS["input_levels"]})
        mock_set.assert_not_called()


async def test_levels_callback_master_status_merged(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    coord.async_set_updated_data(dict(MOCK_STATUS))
    cb = await _get_callback(coord, mock_api)

    with patch.object(coord, "async_set_updated_data", Mock()) as mock_set:
        await cb({"master_status": {"volume": -40.0, "mute": True}})
        mock_set.assert_called_once()
        updated = mock_set.call_args[0][0]
        assert updated["master"]["volume"] == -40
        assert updated["master"]["mute"] is True
        # Other master fields preserved
        assert "source" in updated["master"]


async def test_levels_callback_outputs_replaced(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    coord.async_set_updated_data(dict(MOCK_STATUS))
    cb = await _get_callback(coord, mock_api)

    new_outputs = [{"index": 0, "gain": -3.0}]
    with patch.object(coord, "async_set_updated_data", Mock()) as mock_set:
        await cb({"outputs": new_outputs})
        mock_set.assert_called_once()
        updated = mock_set.call_args[0][0]
        assert updated["outputs"] == new_outputs


async def test_levels_callback_nested_levels_dict(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    coord.async_set_updated_data(dict(MOCK_STATUS))
    cb = await _get_callback(coord, mock_api)

    new_out = [-20, -20, -25, -25]
    with patch.object(coord, "async_set_updated_data", Mock()) as mock_set:
        await cb({"levels": {"output_levels": new_out}})
        mock_set.assert_called_once()
        updated = mock_set.call_args[0][0]
        assert updated["output_levels"] == new_out


# ---------------------------------------------------------------------------
# async_disconnect
# ---------------------------------------------------------------------------


async def test_disconnect_calls_api_and_unsubscribe(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    await coord.async_start()
    await coord.async_disconnect()
    mock_api.unsubscribe_mock.assert_called_once()
    mock_api.async_disconnect.assert_awaited_once()


def test_health_poll_interval_is_enabled(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    assert coord.update_interval is not None
    assert coord.update_interval.total_seconds() == HEALTH_POLL_INTERVAL_SECONDS


def test_ws_available_uses_connection_state(hass, mock_api):
    coord = _make_coordinator(hass, mock_api)
    mock_api.ws_connected = False
    coord._last_ws_msg_at = None
    assert coord.ws_available is False

    mock_api.ws_connected = True
    assert coord.ws_available is True
