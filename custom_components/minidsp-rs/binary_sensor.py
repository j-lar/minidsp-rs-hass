from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)


class MiniDSPConnectionSensor(CoordinatorEntity[MiniDSPCoordinator], BinarySensorEntity):
    """Binary sensor indicating whether the device is reachable."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_connected"
        )
        self._attr_name = "Connected"

    @property
    def is_on(self):  # type: ignore[override]
        return self.coordinator.http_available

    @property
    def extra_state_attributes(self):  # type: ignore[override]
        return {
            "http_available": self.coordinator.http_available,
            "ws_available": self.coordinator.ws_available,
            "ws_connected": self.coordinator.api.ws_connected,
            "last_http_ok": self.coordinator.last_http_ok,
            "last_ws_msg_at": self.coordinator.last_ws_msg_at,
        }

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: MiniDSPCoordinator | None = stored.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not found during binary_sensor setup")
        return

    async_add_entities([MiniDSPConnectionSensor(coordinator)])
