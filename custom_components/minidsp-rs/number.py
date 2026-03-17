from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MASTER_VOLUME_MIN_DB,
    MASTER_VOLUME_MAX_DB,
    OUTPUT_GAIN_MIN_DB,
    OUTPUT_GAIN_MAX_DB,
)
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)


class MiniDSPMasterGain(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """Master volume as a precise dB number entity (-127 to 0 dB)."""

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
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


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
        self._attr_name = f"Output {output_index + 1} Gain"

    @property
    def native_value(self):  # type: ignore[override]
        for output in (self.coordinator.data or {}).get("outputs", []):
            if output.get("index") == self._output_index:
                return output.get("gain")
        return None

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_output_gain(self._output_index, float(value))
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPInputGain(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """Input channel gain control (-127 to 12 dB)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:microphone"
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
        self._attr_name = f"Input {input_index + 1} Gain"

    @property
    def native_value(self):  # type: ignore[override]
        for inp in (self.coordinator.data or {}).get("inputs", []):
            if inp.get("index") == self._input_index:
                return inp.get("gain")
        return None

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_input_gain(self._input_index, float(value))
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPOutputDelay(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """Output channel delay control (0 to 1000 ms)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 1000.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "ms"

    def __init__(self, coordinator: MiniDSPCoordinator, output_index: int):
        super().__init__(coordinator)
        self._output_index = output_index
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_output_{output_index}_delay"
        )
        self._attr_name = f"Output {output_index + 1} Delay"

    @property
    def native_value(self):  # type: ignore[override]
        for output in (self.coordinator.data or {}).get("outputs", []):
            if output.get("index") == self._output_index:
                delay = output.get("delay")
                if delay is None:
                    return None
                # Duration is {secs, nanos} — convert to milliseconds
                return delay.get("secs", 0) * 1000.0 + delay.get("nanos", 0) / 1_000_000.0
        return None

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_output_delay(self._output_index, float(value))
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MiniDSPOutputCompressorNumber(CoordinatorEntity[MiniDSPCoordinator], NumberEntity):
    """A single numeric parameter of the output compressor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:sine-wave"
    _attr_native_step = 0.01

    # Per-parameter metadata: (min, max, unit, icon)
    _PARAM_META: dict[str, tuple[float, float, str, str]] = {
        "threshold": (-80.0, 0.0, "dBFS", "mdi:sine-wave"),
        "ratio":     (1.0, 100.0, ":1", "mdi:division"),
        "attack":    (0.0, 2000.0, "ms", "mdi:timer-outline"),
        "release":   (0.0, 2000.0, "ms", "mdi:timer-outline"),
    }

    def __init__(
        self, coordinator: MiniDSPCoordinator, output_index: int, param: str
    ):
        super().__init__(coordinator)
        self._output_index = output_index
        self._param = param
        meta = self._PARAM_META[param]
        self._attr_native_min_value = meta[0]
        self._attr_native_max_value = meta[1]
        self._attr_native_unit_of_measurement = meta[2]
        self._attr_icon = meta[3]
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}"
            f"_output_{output_index}_compressor_{param}"
        )
        self._attr_name = f"Output {output_index + 1} Compressor {param.capitalize()}"

    def _compressor_data(self) -> dict[str, Any]:
        for output in (self.coordinator.data or {}).get("outputs", []):
            if output.get("index") == self._output_index:
                return output.get("compressor") or {}
        return {}

    @property
    def native_value(self):  # type: ignore[override]
        return self._compressor_data().get(self._param)

    async def async_set_native_value(self, value: float):  # type: ignore[override]
        await self.coordinator.api.async_set_output_compressor(
            self._output_index, **{self._param: float(value)}
        )
        self.coordinator.async_schedule_refresh()

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
    num_inputs = len(data.get("input_levels", []))
    num_outputs = len(data.get("output_levels", []))

    has_compressor = coordinator.profile.get("has_compressor", False)

    entities: list[NumberEntity] = [MiniDSPMasterGain(coordinator)]

    for i in range(num_outputs):
        entities.append(MiniDSPOutputGain(coordinator, i))
        entities.append(MiniDSPOutputDelay(coordinator, i))
        if has_compressor:
            for param in MiniDSPOutputCompressorNumber._PARAM_META:
                entities.append(MiniDSPOutputCompressorNumber(coordinator, i, param))

    for i in range(num_inputs):
        entities.append(MiniDSPInputGain(coordinator, i))

    async_add_entities(entities)
