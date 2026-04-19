"""Tests for diagnostic binary sensors."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("custom_components.minidsp-rs.binary_sensor")
MiniDSPConnectionSensor = _mod.MiniDSPConnectionSensor


def test_connection_sensor_uses_http_availability(mock_coordinator):
    sensor = MiniDSPConnectionSensor(mock_coordinator)
    mock_coordinator.http_available = True
    assert sensor.is_on is True

    mock_coordinator.http_available = False
    assert sensor.is_on is False


def test_connection_sensor_attributes_include_transport_state(mock_coordinator):
    sensor = MiniDSPConnectionSensor(mock_coordinator)
    attrs = sensor.extra_state_attributes

    assert attrs["http_available"] == mock_coordinator.http_available
    assert attrs["ws_available"] == mock_coordinator.ws_available
    assert attrs["ws_connected"] == mock_coordinator.api.ws_connected
    assert attrs["last_http_ok"] == mock_coordinator.last_http_ok
    assert attrs["last_ws_msg_at"] == mock_coordinator.last_ws_msg_at
