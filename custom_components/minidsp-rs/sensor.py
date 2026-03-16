from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)


class _LevelSensorBase(CoordinatorEntity[MiniDSPCoordinator], SensorEntity):
    _attr_native_unit_of_measurement = "dBFS"
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: MiniDSPCoordinator, name: str, index: int, key: str
    ):
        super().__init__(coordinator)
        self._key = key  # "input_levels" or "output_levels"
        self._index = index
        self._attr_unique_id = f"{coordinator.address}_{key}_{index}"
        self._attr_name = name

    @property
    def native_value(self):  # type: ignore[override]
        levels: list[Any] | None = (self.coordinator.data or {}).get(self._key)
        if levels and len(levels) > self._index:
            try:
                return int(round(float(levels[self._index])))
            except (TypeError, ValueError):
                return None
        return None

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPProfileSensor(CoordinatorEntity[MiniDSPCoordinator], SensorEntity):
    """Diagnostic sensor showing the selected device profile/model."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_profile"
        self._attr_name = "Device Profile"

    @property
    def native_value(self):  # type: ignore[override]
        return self.coordinator.profile_name

    @property
    def extra_state_attributes(self):
        info = self.coordinator.device_info or {}
        attrs = {}
        if info:
            if "product_name" in info:
                attrs["product_name"] = info["product_name"]
            if "url" in info:
                attrs["device_url"] = info["url"]
        return attrs

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPVersionSensor(CoordinatorEntity[MiniDSPCoordinator], SensorEntity):
    """Diagnostic sensor exposing a hardware version field (hw_id, dsp_version, serial)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    _FIELD_NAMES = {
        "hw_id": "Hardware ID",
        "dsp_version": "DSP Version",
        "serial": "Serial Number",
    }

    def __init__(self, coordinator: MiniDSPCoordinator, field: str):
        super().__init__(coordinator)
        self._field = field
        self._attr_unique_id = f"{coordinator.address}_{field}"
        self._attr_name = self._FIELD_NAMES[field]

    @property
    def native_value(self):  # type: ignore[override]
        version = (self.coordinator.device_info or {}).get("version") or {}
        return version.get(self._field)

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: MiniDSPCoordinator | None = stored.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not found during sensor platform setup")
        return

    # Determine how many channels we have based on initial data
    data = coordinator.data or {}

    entities: list[SensorEntity] = []

    entities.append(MiniDSPProfileSensor(coordinator))

    # Hardware version diagnostics (only if version data is available)
    version = (coordinator.device_info or {}).get("version")
    if version:
        for field in ("hw_id", "dsp_version", "serial"):
            entities.append(MiniDSPVersionSensor(coordinator, field))

    for key in ("input_levels", "output_levels"):
        levels = data.get(key, [])
        for idx, _ in enumerate(levels):
            friendly = "Input" if key == "input_levels" else "Output"
            name = f"{friendly} Level {idx + 1}"
            entities.append(_LevelSensorBase(coordinator, name, idx, key))

    async_add_entities(entities)
