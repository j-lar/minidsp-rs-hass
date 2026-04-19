"""Tests for MiniDSPAPI — HTTP client and WebSocket handling."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import importlib

import pytest

_api_mod = importlib.import_module("custom_components.minidsp-rs.api")
MiniDSPAPI = _api_mod.MiniDSPAPI

from .conftest import BASE_URL, MOCK_DEVICES, MOCK_STATUS


# ---------------------------------------------------------------------------
# Helpers — build a mock aiohttp ClientSession
# ---------------------------------------------------------------------------


def _make_session(json_return: Any = None, status: int = 200):
    """Return a mock aiohttp ClientSession whose responses return *json_return*."""
    resp = AsyncMock()
    resp.raise_for_status = MagicMock()
    resp.json = AsyncMock(return_value=json_return)
    resp.status = status
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=resp)
    session.post = MagicMock(return_value=resp)
    return session, resp


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def test_async_get_status():
    session, resp = _make_session(MOCK_STATUS)
    api = MiniDSPAPI(BASE_URL, session)
    result = await api.async_get_status()
    assert result == MOCK_STATUS
    session.get.assert_called_once_with(f"{BASE_URL}/devices/0", timeout=ANY)
    resp.raise_for_status.assert_called_once()


async def test_async_get_devices():
    session, resp = _make_session(MOCK_DEVICES)
    api = MiniDSPAPI(BASE_URL, session)
    result = await api.async_get_devices()
    assert result == MOCK_DEVICES
    session.get.assert_called_once_with(f"{BASE_URL}/devices", timeout=ANY)


async def test_async_post_config():
    session, resp = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    payload = {"master_status": {"volume": -30.0}}
    await api.async_post_config(payload)
    session.post.assert_called_once_with(
        f"{BASE_URL}/devices/0/config", json=payload, timeout=ANY
    )
    resp.raise_for_status.assert_called_once()


async def test_device_index_respected():
    """API uses the configured device index in all URLs."""
    session, _ = _make_session(MOCK_STATUS)
    api = MiniDSPAPI(BASE_URL, session, device_index=2)
    await api.async_get_status()
    session.get.assert_called_once_with(f"{BASE_URL}/devices/2", timeout=ANY)


# ---------------------------------------------------------------------------
# Convenience setters — all delegate to async_post_config
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,kwargs,expected_payload",
    [
        ("async_set_volume", {"gain": -30.0}, {"master_status": {"volume": -30.0}}),
        ("async_set_mute", {"mute": True}, {"master_status": {"mute": True}}),
        ("async_set_dirac", {"enabled": False}, {"master_status": {"dirac": False}}),
        ("async_set_source", {"source": "Usb"}, {"master_status": {"source": "Usb"}}),
        ("async_set_preset", {"preset": 2}, {"master_status": {"preset": 2}}),
        (
            "async_set_output_gain",
            {"output_index": 1, "gain": -6.0},
            {"outputs": [{"index": 1, "gain": -6.0}]},
        ),
    ],
)
async def test_convenience_setters(method, kwargs, expected_payload):
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    await getattr(api, method)(**kwargs)
    session.post.assert_called_once_with(
        f"{BASE_URL}/devices/0/config", json=expected_payload, timeout=ANY
    )


# ---------------------------------------------------------------------------
# _build_ws_url
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base_url,expected_prefix",
    [
        ("http://localhost:5380", "ws://localhost:5380"),
        ("https://example.com:5380", "wss://example.com:5380"),
        ("tcp://192.168.1.10:5380", "ws://192.168.1.10:5380"),
        ("ws://localhost:5380", "ws://localhost:5380"),
    ],
)
def test_build_ws_url(base_url, expected_prefix):
    api = MiniDSPAPI(base_url, MagicMock())
    url = api._build_ws_url()
    assert url.startswith(expected_prefix)
    assert "/devices/0" in url
    assert "levels=true" in url
    assert "poll=true" in url


# ---------------------------------------------------------------------------
# Subscription / unsubscribe
# ---------------------------------------------------------------------------


async def test_subscribe_adds_listener():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    cb = AsyncMock()
    with patch.object(api, "_ws_listener_task", new=AsyncMock()):
        api._ws_task = asyncio.create_task(asyncio.sleep(0))  # fake running task
        unsub = await api.async_subscribe_levels(cb)
        assert cb in api._listeners
        unsub()
        assert cb not in api._listeners


async def test_unsubscribe_sets_stop_when_last_listener():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    cb = AsyncMock()
    api._listeners.append(cb)
    api._stop_event = asyncio.Event()
    # Manually build unsubscribe closure by subscribing then getting the result
    with patch.object(asyncio, "create_task", return_value=MagicMock()):
        unsub = await api.async_subscribe_levels(cb)
    # Remove the duplicate that subscribe added
    api._listeners.clear()
    api._listeners.append(cb)
    unsub()
    assert api._stop_event.is_set()


async def test_subscribe_restarts_when_ws_task_is_done():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    cb = AsyncMock()
    done_task = asyncio.create_task(asyncio.sleep(0))
    await done_task
    api._ws_task = done_task
    api._stop_event.set()

    new_task = MagicMock()
    with patch.object(asyncio, "create_task", return_value=new_task) as mock_create:
        await api.async_subscribe_levels(cb)

    mock_create.assert_called_once()
    assert api._ws_task is new_task
    assert not api._stop_event.is_set()


async def test_disconnect_then_subscribe_resets_stop_event():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    cb = AsyncMock()
    api._ws_task = asyncio.create_task(asyncio.sleep(0))
    await api.async_disconnect()
    assert api._ws_task is None
    assert api._stop_event.is_set()

    with patch.object(asyncio, "create_task", return_value=MagicMock()):
        await api.async_subscribe_levels(cb)
    assert not api._stop_event.is_set()


async def test_ws_listener_cleanup_after_unexpected_failure():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    api._stop_event = asyncio.Event()

    async def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    session.ws_connect = _boom
    sleep_calls = 0

    async def _fake_sleep(_delay):
        nonlocal sleep_calls
        sleep_calls += 1
        api._stop_event.set()

    with patch.object(asyncio, "sleep", new=_fake_sleep):
        await api._ws_listener_task()

    assert sleep_calls == 1
    assert api._ws_task is None


# ---------------------------------------------------------------------------
# _dispatch_event
# ---------------------------------------------------------------------------


async def test_dispatch_event_calls_all_listeners():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)
    cb1 = AsyncMock()
    cb2 = AsyncMock()
    api._listeners = [cb1, cb2]
    event = {"input_levels": [1, 2]}
    await api._dispatch_event(event)
    cb1.assert_awaited_once_with(event)
    cb2.assert_awaited_once_with(event)


async def test_dispatch_event_exception_does_not_stop_others():
    session, _ = _make_session()
    api = MiniDSPAPI(BASE_URL, session)

    async def _bad_cb(event):
        raise RuntimeError("boom")

    good_cb = AsyncMock()
    api._listeners = [_bad_cb, good_cb]
    await api._dispatch_event({"test": True})
    good_cb.assert_awaited_once()
