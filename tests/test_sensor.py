"""Tests for sensor entities."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import pytest

_mod = importlib.import_module("custom_components.minidsp-rs.sensor")
MiniDSPProfileSensor = _mod.MiniDSPProfileSensor
_LevelSensorBase = _mod._LevelSensorBase

from .conftest import BASE_URL, MOCK_STATUS


def _level_sensor(mock_coordinator, key="input_levels", index=0, name=None):
    name = name or f"{'Input' if key == 'input_levels' else 'Output'} Level {index + 1}"
    return _LevelSensorBase(mock_coordinator, name, index, key)


# ---------------------------------------------------------------------------
# _LevelSensorBase
# ---------------------------------------------------------------------------


def test_input_level_native_value(mock_coordinator):
    sensor = _level_sensor(mock_coordinator, "input_levels", 0)
    assert sensor.native_value == -10


def test_output_level_native_value(mock_coordinator):
    sensor = _level_sensor(mock_coordinator, "output_levels", 2)
    assert sensor.native_value == -20


def test_level_sensor_rounds_to_int(mock_coordinator):
    mock_coordinator.data["input_levels"] = [-10.7, -9.3]
    sensor = _level_sensor(mock_coordinator, "input_levels", 0)
    assert sensor.native_value == -11
    sensor2 = _level_sensor(mock_coordinator, "input_levels", 1)
    assert sensor2.native_value == -9


def test_level_sensor_out_of_bounds_returns_none(mock_coordinator):
    sensor = _level_sensor(mock_coordinator, "input_levels", 99)
    assert sensor.native_value is None


def test_level_sensor_missing_data_returns_none(mock_coordinator):
    mock_coordinator.data = {}
    sensor = _level_sensor(mock_coordinator, "input_levels", 0)
    assert sensor.native_value is None


def test_level_sensor_name_is_1indexed(mock_coordinator):
    sensor = _level_sensor(mock_coordinator, "input_levels", 0)
    assert sensor._attr_name == "Input Level 1"

    sensor2 = _level_sensor(mock_coordinator, "output_levels", 2)
    assert sensor2._attr_name == "Output Level 3"


def test_level_sensor_unique_id(mock_coordinator):
    sensor = _level_sensor(mock_coordinator, "input_levels", 0)
    assert "input_levels" in sensor._attr_unique_id
    assert "0" in sensor._attr_unique_id


def test_level_sensor_device_info_from_coordinator(mock_coordinator):
    sensor = _level_sensor(mock_coordinator, "input_levels", 0)
    assert sensor.device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# MiniDSPProfileSensor
# ---------------------------------------------------------------------------


def test_profile_sensor_value(mock_coordinator):
    sensor = MiniDSPProfileSensor(mock_coordinator)
    assert sensor.native_value == mock_coordinator.profile_name


def test_profile_sensor_attributes_with_device_info(mock_coordinator):
    mock_coordinator.device_info = {"product_name": "2x4 HD", "url": BASE_URL}
    sensor = MiniDSPProfileSensor(mock_coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs.get("product_name") == "2x4 HD"
    assert attrs.get("device_url") == BASE_URL


def test_profile_sensor_attributes_no_device_info(mock_coordinator):
    mock_coordinator.device_info = None
    sensor = MiniDSPProfileSensor(mock_coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs == {}


def test_profile_sensor_device_info_from_coordinator(mock_coordinator):
    sensor = MiniDSPProfileSensor(mock_coordinator)
    assert sensor.device_info == mock_coordinator.ha_device_info


# ---------------------------------------------------------------------------
# async_setup_entry entity creation
# ---------------------------------------------------------------------------


async def test_setup_entry_creates_level_and_profile_entities(hass, real_coordinator):
    _sensor_mod = importlib.import_module("custom_components.minidsp-rs.sensor")
    async_setup_entry = _sensor_mod.async_setup_entry
    _const = importlib.import_module("custom_components.minidsp-rs.const")
    DOMAIN = _const.DOMAIN
    from homeassistant.config_entries import ConfigEntry

    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": real_coordinator
    }

    added = []

    def _add(entities, **kwargs):
        added.extend(entities)

    await async_setup_entry(hass, entry, _add)

    types = [type(e).__name__ for e in added]
    assert "MiniDSPProfileSensor" in types
    # 2 inputs + 4 outputs from MOCK_STATUS
    level_sensors = [e for e in added if isinstance(e, _LevelSensorBase)]
    assert len(level_sensors) == 6
