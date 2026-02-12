from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MASTER_VOLUME_MAX_DB,
    MASTER_VOLUME_MIN_DB,
    OUTPUT_GAIN_MAX_DB,
    OUTPUT_GAIN_MIN_DB,
)
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)


class MiniDSPOutputGain(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """Output channel gain control (-127 to 12 dB)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:volume-high"
    _attr_native_min_value = OUTPUT_GAIN_MIN_DB
    _attr_native_max_value = OUTPUT_GAIN_MAX_DB
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dBFS"

    def __init__(self, coordinator: MiniDSPCoordinator, output_index: int):
        super().__init__(coordinator)
        self._output_index = output_index
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_output_{output_index}_gain"
        )
        self._attr_name = f"Output {output_index} Gain"

    @property
    def native_value(self):  # type: ignore[override]
        # Try to get current gain from outputs data if available
        outputs = (self.coordinator.data or {}).get("outputs", [])
        for output in outputs:
            if output.get("index") == self._output_index:
                return output.get("gain")
        return None

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_output_gain(
            self._output_index, float(value)
        )
        # Force refresh to reflect new value
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPMasterGain(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """Master volume as a precise dB number entity."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:knob"
    _attr_native_min_value = MASTER_VOLUME_MIN_DB
    _attr_native_max_value = MASTER_VOLUME_MAX_DB
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_master_gain"
        )
        self._attr_name = "Master Volume"

    @property
    def native_value(self):  # type: ignore[override]
        return self.coordinator.get_master_value("volume")

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_volume(float(value))
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPInputGain(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """Input channel gain control."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:volume-source"
    _attr_native_min_value = OUTPUT_GAIN_MIN_DB
    _attr_native_max_value = OUTPUT_GAIN_MAX_DB
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dBFS"

    def __init__(self, coordinator: MiniDSPCoordinator, input_index: int):
        super().__init__(coordinator)
        self._input_index = input_index
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_input_{input_index}_gain"
        )
        self._attr_name = f"Input {input_index} Gain"

    @property
    def native_value(self):  # type: ignore[override]
        inputs = (self.coordinator.data or {}).get("inputs", [])
        for inp in inputs:
            if inp.get("index") == self._input_index:
                return inp.get("gain")
        return None

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_input_gain(
            self._input_index, float(value)
        )
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: MiniDSPCoordinator | None = stored.get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not found during number platform setup")
        return

    data = coordinator.data or {}
    entities: list[NumberEntity] = []

    # Master volume as precise dB slider
    entities.append(MiniDSPMasterGain(coordinator))

    # Per-output gain sliders
    output_levels = data.get("output_levels", [])
    for i in range(len(output_levels)):
        entities.append(MiniDSPOutputGain(coordinator, i))

    # Per-input gain sliders
    input_levels = data.get("input_levels", [])
    for i in range(len(input_levels)):
        entities.append(MiniDSPInputGain(coordinator, i))

    async_add_entities(entities)
