from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiniDSPCoordinator

_LOGGER = logging.getLogger(__name__)


class DiracLiveSwitch(CoordinatorEntity[MiniDSPCoordinator], SwitchEntity):
    """Switch to enable/disable Dirac Live."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:autorenew"

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_dirac"
        )
        self._attr_name = "Dirac Live"

    @property
    def is_on(self):  # type: ignore[override]
        return self.coordinator.get_master_value("dirac")

    async def async_turn_on(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_dirac(True)
        self.coordinator.async_schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_dirac(False)
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class MuteSwitch(CoordinatorEntity[MiniDSPCoordinator], SwitchEntity):
    """Switch to toggle master mute."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:volume-mute"

    def __init__(self, coordinator: MiniDSPCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_mute"
        )
        self._attr_name = "Mute"

    @property
    def is_on(self):  # type: ignore[override]
        return self.coordinator.get_master_value("mute")

    async def async_turn_on(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_mute(True)
        self.coordinator.async_schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_mute(False)
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class OutputMuteSwitch(CoordinatorEntity[MiniDSPCoordinator], SwitchEntity):
    """Switch to mute a single output channel."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:volume-off"

    def __init__(self, coordinator: MiniDSPCoordinator, output_index: int):
        super().__init__(coordinator)
        self._output_index = output_index
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_output_{output_index}_mute"
        )
        self._attr_name = f"Output {output_index + 1} Mute"

    def _output_data(self) -> dict[str, Any]:
        for output in (self.coordinator.data or {}).get("outputs", []):
            if output.get("index") == self._output_index:
                return output
        return {}

    @property
    def is_on(self):  # type: ignore[override]
        return self._output_data().get("mute")

    async def async_turn_on(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_output_mute(self._output_index, True)
        self.coordinator.async_schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_output_mute(self._output_index, False)
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class InputMuteSwitch(CoordinatorEntity[MiniDSPCoordinator], SwitchEntity):
    """Switch to mute a single input channel."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:microphone-off"

    def __init__(self, coordinator: MiniDSPCoordinator, input_index: int):
        super().__init__(coordinator)
        self._input_index = input_index
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}_input_{input_index}_mute"
        )
        self._attr_name = f"Input {input_index + 1} Mute"

    def _input_data(self) -> dict[str, Any]:
        for inp in (self.coordinator.data or {}).get("inputs", []):
            if inp.get("index") == self._input_index:
                return inp
        return {}

    @property
    def is_on(self):  # type: ignore[override]
        return self._input_data().get("mute")

    async def async_turn_on(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_input_mute(self._input_index, True)
        self.coordinator.async_schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_input_mute(self._input_index, False)
        self.coordinator.async_schedule_refresh()

    @property
    def device_info(self):  # type: ignore[override]
        return self.coordinator.ha_device_info


class OutputCompressorBypassSwitch(CoordinatorEntity[MiniDSPCoordinator], SwitchEntity):
    """Switch to bypass the compressor on a single output channel."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:audio-input-rca"

    def __init__(self, coordinator: MiniDSPCoordinator, output_index: int):
        super().__init__(coordinator)
        self._output_index = output_index
        self._attr_unique_id = (
            f"{coordinator.address}_d{coordinator.device_index}"
            f"_output_{output_index}_compressor_bypass"
        )
        self._attr_name = f"Output {output_index + 1} Compressor Bypass"

    def _compressor_data(self) -> dict[str, Any]:
        for output in (self.coordinator.data or {}).get("outputs", []):
            if output.get("index") == self._output_index:
                return output.get("compressor") or {}
        return {}

    @property
    def is_on(self):  # type: ignore[override]
        return self._compressor_data().get("bypass")

    async def async_turn_on(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_output_compressor(
            self._output_index, bypass=True
        )
        self.coordinator.async_schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.coordinator.api.async_set_output_compressor(
            self._output_index, bypass=False
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
        _LOGGER.error("Coordinator not found during switch platform setup")
        return

    data = coordinator.data or {}
    num_inputs = len(data.get("input_levels", []))
    num_outputs = len(data.get("output_levels", []))

    entities: list[SwitchEntity] = [DiracLiveSwitch(coordinator), MuteSwitch(coordinator)]

    for i in range(num_outputs):
        entities.append(OutputMuteSwitch(coordinator, i))
        entities.append(OutputCompressorBypassSwitch(coordinator, i))

    for i in range(num_inputs):
        entities.append(InputMuteSwitch(coordinator, i))

    async_add_entities(entities)
