from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, build_preset_maps, build_source_maps
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)


class PresetSelect(CoordinatorEntity[MiniDSPCoordinator], SelectEntity):
    """Select entity for MiniDSP configuration presets."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:playlist-music"

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_preset"
        self._attr_name = "Preset"
        self._label_to_index, self._index_to_label = build_preset_maps(
            coordinator.profile
        )

    @property
    def current_option(self):  # type: ignore[override]
        idx = (self.coordinator.data or {}).get("master", {}).get("preset")
        if idx is None:
            return None
        return self._index_to_label.get(idx)

    @property
    def options(self):  # type: ignore[override]
        return list(self._label_to_index.keys())

    async def async_select_option(self, option: str) -> None:  # type: ignore[override]
        if option not in self._label_to_index:
            _LOGGER.warning("Unknown preset option %s", option)
            return
        await self.coordinator._api.async_set_preset(self._label_to_index[option])
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "name": self.coordinator.name,
        }


class SourceSelect(CoordinatorEntity[MiniDSPCoordinator], SelectEntity):
    """Select entity for MiniDSP input source."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:audio-input-rca"

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_source"
        self._attr_name = "Source"
        self._label_to_api, self._api_to_label = build_source_maps(coordinator.profile)

    @property
    def current_option(self):  # type: ignore[override]
        raw = (self.coordinator.data or {}).get("master", {}).get("source")
        if raw is None:
            return None
        return self._api_to_label.get(raw, raw)

    @property
    def options(self):  # type: ignore[override]
        return list(self._label_to_api.keys())

    async def async_select_option(self, option: str) -> None:  # type: ignore[override]
        api_val = self._label_to_api.get(option, option)
        await self.coordinator._api.async_set_source(api_val)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "name": self.coordinator.name,
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: MiniDSPCoordinator | None = stored.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not found during select platform setup")
        return

    async_add_entities([PresetSelect(coordinator), SourceSelect(coordinator)])
