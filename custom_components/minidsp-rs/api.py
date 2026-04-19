from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Coroutine

import aiohttp

_LOGGER = logging.getLogger(__name__)


class MiniDSPAPI:
    """Simple async wrapper around the minidsp-rs HTTP & WebSocket API."""

    _TIMEOUT = aiohttp.ClientTimeout(total=10)

    def __init__(
        self, base_url: str, session: aiohttp.ClientSession, device_index: int = 0
    ):
        # Normalise base url (strip trailing slash, convert ws:// → http://)
        self._base_url = self._normalize_base_url(base_url).rstrip("/")
        self._session = session
        self._device_index = device_index
        self._ws_task: asyncio.Task | None = None
        self._listeners: list[
            Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
        ] = []
        self._stop_event = asyncio.Event()
        self._last_ws_msg_at: float | None = None
        self._ws_connected = False

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    async def async_get_status(self) -> dict[str, Any]:
        """Return the status summary for the device."""
        url = f"{self._base_url}/devices/{self._device_index}"
        async with self._session.get(url, timeout=self._TIMEOUT) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return list of available devices from the daemon."""
        url = f"{self._base_url}/devices"
        async with self._session.get(url, timeout=self._TIMEOUT) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_post_config(self, payload: dict[str, Any]) -> None:
        """POST configuration changes to the device.

        Retries once on transient network errors.
        """
        url = f"{self._base_url}/devices/{self._device_index}/config"
        try:
            async with self._session.post(
                url, json=payload, timeout=self._TIMEOUT
            ) as resp:
                resp.raise_for_status()
                return
        except (aiohttp.ClientError, asyncio.TimeoutError) as first_err:
            _LOGGER.debug("First POST attempt failed (%s), retrying", first_err)

        await asyncio.sleep(0.5)
        async with self._session.post(
            url, json=payload, timeout=self._TIMEOUT
        ) as resp:
            resp.raise_for_status()

    # ----------------------- convenience setters ------------------------

    async def async_set_volume(self, gain: float) -> None:
        await self.async_post_config({"master_status": {"volume": gain}})

    async def async_set_mute(self, mute: bool) -> None:
        await self.async_post_config({"master_status": {"mute": mute}})

    async def async_set_dirac(self, enabled: bool) -> None:
        await self.async_post_config({"master_status": {"dirac": enabled}})

    async def async_set_source(self, source: str) -> None:
        await self.async_post_config({"master_status": {"source": source}})

    async def async_set_preset(self, preset: int) -> None:
        await self.async_post_config({"master_status": {"preset": preset}})

    async def async_set_output_gain(self, output_index: int, gain: float) -> None:
        await self.async_post_config(
            {"outputs": [{"index": output_index, "gain": gain}]}
        )

    async def async_set_output_mute(self, output_index: int, mute: bool) -> None:
        await self.async_post_config(
            {"outputs": [{"index": output_index, "mute": mute}]}
        )

    async def async_set_output_delay(
        self, output_index: int, milliseconds: float
    ) -> None:
        total_ns = int(milliseconds * 1_000_000)
        secs = total_ns // 1_000_000_000
        nanos = total_ns % 1_000_000_000
        await self.async_post_config(
            {"outputs": [{"index": output_index, "delay": {"secs": secs, "nanos": nanos}}]}
        )

    async def async_set_output_compressor(
        self,
        output_index: int,
        *,
        attack: float | None = None,
        release: float | None = None,
        ratio: float | None = None,
        threshold: float | None = None,
        bypass: bool | None = None,
    ) -> None:
        compressor: dict[str, Any] = {}
        if attack is not None:
            compressor["attack"] = attack
        if release is not None:
            compressor["release"] = release
        if ratio is not None:
            compressor["ratio"] = ratio
        if threshold is not None:
            compressor["threshold"] = threshold
        if bypass is not None:
            compressor["bypass"] = bypass
        await self.async_post_config(
            {"outputs": [{"index": output_index, "compressor": compressor}]}
        )

    async def async_set_input_gain(self, input_index: int, gain: float) -> None:
        await self.async_post_config(
            {"inputs": [{"index": input_index, "gain": gain}]}
        )

    async def async_set_input_mute(self, input_index: int, mute: bool) -> None:
        await self.async_post_config(
            {"inputs": [{"index": input_index, "mute": mute}]}
        )

    # ----------------------- websocket handling -------------------------

    async def async_subscribe_levels(
        self, callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
    ) -> Callable[[], None]:
        """Subscribe to live level updates.

        The callback will receive a dict containing at least `input_levels` and
        `output_levels` whenever a new message is received.
        Returns an unsubscribe callback.
        """
        self._listeners.append(callback)

        if self._ws_task is None or self._ws_task.done():
            self._stop_event.clear()
            self._ws_task = asyncio.create_task(self._ws_listener_task())

        def _unsubscribe() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)
            if not self._listeners:
                self._stop_event.set()

        return _unsubscribe

    async def async_disconnect(self) -> None:
        """Cancel the websocket task (if any)."""
        self._stop_event.set()
        if self._ws_task:
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._ws_task = None
        self._ws_connected = False

    # ---------------------------------------------------------------------

    async def _ws_listener_task(self) -> None:
        """Background task that maintains the websocket connection."""
        ws_url = self._build_ws_url()
        backoff = 1.0
        try:
            while not self._stop_event.is_set():
                try:
                    _LOGGER.debug("Connecting to MiniDSP websocket at %s", ws_url)
                    async with self._session.ws_connect(ws_url, heartbeat=30) as ws:
                        self._ws_connected = True
                        backoff = 1.0  # Reset backoff after successful connect
                        await self._dispatch_event({"_reconnected": True})
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = json.loads(msg.data)
                                except json.JSONDecodeError as err:
                                    _LOGGER.warning(
                                        "Failed to decode websocket message: %s", err
                                    )
                                    continue
                                self._last_ws_msg_at = time.monotonic()
                                _LOGGER.debug("Websocket message: %s", data)
                                await self._dispatch_event(data)
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                _LOGGER.debug("Websocket closed")
                                break
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                _LOGGER.debug("Websocket error: %s", ws.exception())
                                break
                except asyncio.CancelledError:
                    raise
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Websocket connection failed: %s", err)
                finally:
                    self._ws_connected = False

                if self._stop_event.is_set():
                    break

                # Reconnect with exponential backoff
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, 60.0)
        finally:
            self._ws_connected = False
            self._ws_task = None
            _LOGGER.debug("MiniDSP websocket listener stopped")

    @property
    def ws_connected(self) -> bool:
        """Return whether the websocket is currently connected."""
        return self._ws_connected

    @property
    def last_ws_msg_at(self) -> float | None:
        """Return monotonic timestamp of last received websocket message."""
        return self._last_ws_msg_at

    async def _dispatch_event(self, event: dict[str, Any]) -> None:
        for cb in list(self._listeners):
            try:
                await cb(event)
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Listener raised: %s", err)

    # ---------------------------------------------------------------------

    def _build_ws_url(self) -> str:
        """Convert the base_url to a websocket URL for streaming levels."""
        # Convert http(s) to ws(s)
        if self._base_url.startswith("https://"):
            scheme = "wss://"
            rest = self._base_url[len("https://"):]
        elif self._base_url.startswith("http://"):
            scheme = "ws://"
            rest = self._base_url[len("http://"):]
        elif self._base_url.startswith("tcp://"):
            # minidsp-rs sometimes advertises tcp scheme; treat as ws
            scheme = "ws://"
            rest = self._base_url[len("tcp://"):]
        else:
            # Assume scheme already correct (ws:// or wss://)
            scheme = ""
            rest = self._base_url

        return f"{scheme}{rest}/devices/{self._device_index}?levels=true&poll=true"

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        """Convert ws(s):// base URLs to http(s):// for HTTP requests."""
        if base_url.startswith("ws://"):
            return "http://" + base_url[len("ws://"):]
        if base_url.startswith("wss://"):
            return "https://" + base_url[len("wss://"):]
        return base_url
