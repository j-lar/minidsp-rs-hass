from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MiniDSPAPI
from .const import DOMAIN

# See: https://developers.home-assistant.io/docs/device_registry_index

_LOGGER = logging.getLogger(__name__)

# Precision for level values
# _ROUND_PRECISION = 0


class MiniDSPCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage MiniDSP data fetching and live updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MiniDSPAPI,
        name: str | None = None,
        profile: dict[str, Any] | None = None,
        profile_name: str | None = None,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=name or DOMAIN,
            update_interval=None,
        )
        self._api = api
        self._unsubscribe_ws: Callable[[], None] | None = None
        self.profile = profile or {}
        self.profile_name = profile_name
        self.device_info: dict[str, Any] | None = None
        # Expose to entities
        self.base_url = api._base_url  # pragma: no cover
        self.address = self.base_url  # alias for clarity

    @property
    def ha_device_info(self) -> dict[str, Any]:
        """Return HA device registry info shared by all entities."""
        product_name = (
            (self.device_info or {}).get("product_name") if self.device_info else None
        )
        return {
            "identifiers": {(DOMAIN, self.address)},
            "name": self.name,
            "manufacturer": "MiniDSP",
            "model": product_name or self.profile_name,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self._api.async_get_status()
            return self._rounded_levels(data)
        except Exception as err:
            raise UpdateFailed(err) from err

    # ------------------------------------------------------------------
    async def async_start(self) -> None:
        """Start listening to websocket events."""

        async def _levels_callback(event: dict[str, Any]):
            # On reconnect, fetch a full state refresh to clear any stale data
            if event.get("_reconnected"):
                self.hass.async_create_task(self.async_request_refresh())
                return

            # Update only levels fields without re-fetching everything
            current = dict(self.data or {})
            updated = False
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
                incoming_master = event.get("master_status") or event.get("master")
                if isinstance(incoming_master, dict):
                    if "master" not in current or not isinstance(
                        current["master"], dict
                    ):
                        current["master"] = {}

                    # Round numeric fields and merge
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
                current["inputs"] = event["inputs"]
                updated = True

            if "outputs" in event and isinstance(event["outputs"], list):
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

            if updated:
                # Push incremental update to listeners
                self.async_set_updated_data(current)

        self._unsubscribe_ws = await self._api.async_subscribe_levels(_levels_callback)

    async def async_disconnect(self):
        if self._unsubscribe_ws:
            self._unsubscribe_ws()
            self._unsubscribe_ws = None
        await self._api.async_disconnect()

    def _rounded_levels(self, data: dict[str, Any]) -> dict[str, Any]:
        def _round_val(val: Any):
            return int(round(val)) if isinstance(val, (int, float)) and not isinstance(val, bool) else val

        rounded_data: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, (list, tuple)):
                rounded_data[key] = [_round_val(v) for v in value]
            elif isinstance(value, dict):
                rounded_data[key] = {k: _round_val(v) for k, v in value.items()}
            else:
                rounded_data[key] = _round_val(value)
        return rounded_data
