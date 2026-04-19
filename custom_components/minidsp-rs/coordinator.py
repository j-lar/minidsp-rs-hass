from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MiniDSPAPI
from .const import DEFAULT_LEVEL_INTERVAL, DOMAIN, HEALTH_POLL_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

# How long to wait after the last command before issuing a refresh (seconds).
_REFRESH_DEBOUNCE_SECONDS = 0.3


class MiniDSPCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage MiniDSP data fetching and live updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MiniDSPAPI,
        name: str | None = None,
        profile: dict[str, Any] | None = None,
        profile_name: str | None = None,
        level_update_interval: float = DEFAULT_LEVEL_INTERVAL,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=name or DOMAIN,
            update_interval=timedelta(seconds=HEALTH_POLL_INTERVAL_SECONDS),
        )
        self._api = api
        self._unsubscribe_ws: Callable[[], None] | None = None
        self.profile = profile or {}
        self.profile_name = profile_name
        self.device_info: dict[str, Any] | None = None
        self.device_index: int = api._device_index
        # Expose to entities
        self.base_url = api._base_url
        self.address = self.base_url  # alias for clarity

        self.level_update_interval = level_update_interval
        self._last_level_push: float = 0.0
        self._refresh_debounce_handle: asyncio.TimerHandle | None = None
        self._http_available = False
        self._last_http_ok: float | None = None
        self._last_ws_msg_at: float | None = None

    @property
    def api(self) -> MiniDSPAPI:
        """Public accessor for the underlying API client."""
        return self._api

    @property
    def http_available(self) -> bool:
        """Whether the HTTP status endpoint is currently reachable."""
        return self._http_available

    @property
    def ws_available(self) -> bool:
        """Whether websocket transport looks alive."""
        if self._api.ws_connected:
            return True
        if self._last_ws_msg_at is None:
            return False
        return (time.monotonic() - self._last_ws_msg_at) < (
            HEALTH_POLL_INTERVAL_SECONDS * 2
        )

    @property
    def transport_available(self) -> bool:
        """Composite transport health for diagnostics."""
        return self.http_available

    @property
    def last_http_ok(self) -> float | None:
        """Monotonic timestamp of the most recent successful HTTP refresh."""
        return self._last_http_ok

    @property
    def last_ws_msg_at(self) -> float | None:
        """Monotonic timestamp of the most recent websocket message."""
        return self._last_ws_msg_at

    def get_master_value(self, key: str, default: Any = None) -> Any:
        """Return a value from the master status dict, or *default*."""
        return (self.data or {}).get("master", {}).get(key, default)

    @property
    def ha_device_info(self) -> DeviceInfo:
        """Return a DeviceInfo for the HA device registry."""
        info = self.device_info or {}
        product_name = info.get("product_name")
        return DeviceInfo(
            identifiers={(DOMAIN, self.address)},
            name=self.name,
            manufacturer="MiniDSP",
            model=product_name or self.profile_name,
        )

    def async_schedule_refresh(self) -> None:
        """Schedule a debounced full state refresh.

        Cancels any pending refresh and schedules a new one after
        _REFRESH_DEBOUNCE_SECONDS. Rapid command bursts (e.g. slider drags)
        collapse into a single HTTP GET.
        """
        if self._refresh_debounce_handle is not None:
            self._refresh_debounce_handle.cancel()

        self._refresh_debounce_handle = self.hass.loop.call_later(
            _REFRESH_DEBOUNCE_SECONDS,
            lambda: self.hass.async_create_task(self._do_debounced_refresh()),
        )

    async def _do_debounced_refresh(self) -> None:
        self._refresh_debounce_handle = None
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self._api.async_get_status()
            self._http_available = True
            self._last_http_ok = time.monotonic()
            return self._rounded_levels(data)
        except Exception as err:
            self._http_available = False
            raise UpdateFailed(err) from err

    # ------------------------------------------------------------------
    async def async_start(self) -> None:
        """Start listening to websocket events."""

        async def _levels_callback(event: dict[str, Any]):
            # On reconnect, fetch a full state refresh to clear any stale data
            if event.get("_reconnected"):
                self.hass.async_create_task(self.async_request_refresh())
                return
            self._last_ws_msg_at = time.monotonic()

            # Update only levels fields without re-fetching everything
            current = dict(self.data or {})
            updated = False
            levels_only = True  # track whether only level data changed

            for key in ("input_levels", "output_levels"):
                if key in event:
                    new_list = [
                        int(round(v)) if isinstance(v, (int, float)) else v
                        for v in event[key]
                    ]
                    if new_list != current.get(key):
                        current[key] = new_list
                        updated = True

            # Handle master status updates
            if "master_status" in event or "master" in event:
                levels_only = False
                incoming_master = event.get("master_status") or event.get("master")
                if isinstance(incoming_master, dict):
                    if "master" not in current or not isinstance(
                        current["master"], dict
                    ):
                        current["master"] = {}

                    # Round numeric fields and merge (bool-safe: mute must stay bool)
                    merged_master = dict(current["master"])
                    for m_key, m_val in incoming_master.items():
                        if isinstance(m_val, (int, float)) and not isinstance(m_val, bool):
                            m_val = int(round(m_val))
                        merged_master[m_key] = m_val

                    if merged_master != current["master"]:
                        current["master"] = merged_master
                        updated = True

            # Handle inputs/outputs updates
            if "inputs" in event and isinstance(event["inputs"], list):
                levels_only = False
                current["inputs"] = event["inputs"]
                updated = True

            if "outputs" in event and isinstance(event["outputs"], list):
                levels_only = False
                current["outputs"] = event["outputs"]
                updated = True

            # Nested levels dict
            if "levels" in event and isinstance(event["levels"], dict):
                for key in ("input_levels", "output_levels"):
                    if key in event["levels"]:
                        new_list = [
                            int(round(v)) if isinstance(v, (int, float)) else v
                            for v in event["levels"][key]
                        ]
                        if new_list != current.get(key):
                            current[key] = new_list
                            updated = True

            if not updated:
                return

            # For level-only updates, apply throttling so HA isn't flooded
            # with entity state changes at the full WS polling rate.
            if levels_only and self.level_update_interval > 0.0:
                now = time.monotonic()
                if now - self._last_level_push < self.level_update_interval:
                    return
                self._last_level_push = now

            # Push incremental update to listeners
            self.async_set_updated_data(current)

        self._unsubscribe_ws = await self._api.async_subscribe_levels(_levels_callback)

    async def async_disconnect(self):
        if self._refresh_debounce_handle is not None:
            self._refresh_debounce_handle.cancel()
            self._refresh_debounce_handle = None
        if self._unsubscribe_ws:
            self._unsubscribe_ws()
            self._unsubscribe_ws = None
        await self._api.async_disconnect()

    def _rounded_levels(self, data: dict[str, Any]) -> dict[str, Any]:
        def _round_recursive(val: Any) -> Any:
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return int(round(val))
            if isinstance(val, dict):
                return {k: _round_recursive(v) for k, v in val.items()}
            if isinstance(val, (list, tuple)):
                return [_round_recursive(v) for v in val]
            return val

        return {k: _round_recursive(v) for k, v in data.items()}
