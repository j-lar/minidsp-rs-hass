"""Tests for MiniDSP config flow and options flow."""

from __future__ import annotations

from unittest.mock import MagicMock

import importlib

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_URL

_cf_mod = importlib.import_module("custom_components.minidsp-rs.config_flow")
MiniDSPConfigFlow = _cf_mod.MiniDSPConfigFlow
MiniDSPOptionsFlow = _cf_mod.MiniDSPOptionsFlow

_const_mod = importlib.import_module("custom_components.minidsp-rs.const")
CONF_MODEL = _const_mod.CONF_MODEL
DEVICE_PROFILES = _const_mod.DEVICE_PROFILES
DOMAIN = _const_mod.DOMAIN
PROFILE_2X4HD = _const_mod.PROFILE_2X4HD
PROFILE_GENERIC = _const_mod.PROFILE_GENERIC

from .conftest import BASE_URL


def _make_flow(hass) -> MiniDSPConfigFlow:
    flow = MiniDSPConfigFlow()
    flow.hass = hass
    flow.context = {"source": config_entries.SOURCE_USER}
    flow.handler = DOMAIN
    flow._async_current_entries = MagicMock(return_value=[])
    return flow


# ---------------------------------------------------------------------------
# async_step_user
# ---------------------------------------------------------------------------


async def test_step_user_shows_form(hass):
    flow = _make_flow(hass)
    result = await flow.async_step_user(None)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_step_user_creates_entry(hass):
    flow = _make_flow(hass)
    result = await flow.async_step_user(
        {CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_URL] == BASE_URL
    assert result["data"][CONF_MODEL] == PROFILE_2X4HD


async def test_step_user_default_name_is_url(hass):
    flow = _make_flow(hass)
    result = await flow.async_step_user(
        {CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD}
    )
    assert result["title"] == BASE_URL


async def test_step_user_custom_name(hass):
    from homeassistant.const import CONF_NAME

    flow = _make_flow(hass)
    result = await flow.async_step_user(
        {CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD, CONF_NAME: "Living Room"}
    )
    assert result["title"] == "Living Room"


async def test_step_user_aborts_on_duplicate(hass):
    from unittest.mock import patch as _patch
    from homeassistant.data_entry_flow import AbortFlow

    flow = _make_flow(hass)
    # Simulate HA detecting that the unique_id is already configured
    with _patch.object(
        flow,
        "_abort_if_unique_id_configured",
        side_effect=AbortFlow("already_configured"),
    ):
        with pytest.raises(AbortFlow):
            await flow.async_step_user({CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD})


# ---------------------------------------------------------------------------
# async_get_options_flow is a proper class method
# ---------------------------------------------------------------------------


def test_options_flow_accessor_is_classmethod():
    """HA requires async_get_options_flow as a static/class method, not module-level."""
    assert hasattr(MiniDSPConfigFlow, "async_get_options_flow")
    method = MiniDSPConfigFlow.async_get_options_flow
    assert callable(method)


def test_options_flow_returns_options_flow_instance():
    mock_entry = MagicMock()
    mock_entry.options = {}
    mock_entry.data = {CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD}
    result = MiniDSPConfigFlow.async_get_options_flow(mock_entry)
    assert isinstance(result, MiniDSPOptionsFlow)


# ---------------------------------------------------------------------------
# MiniDSPOptionsFlow
# ---------------------------------------------------------------------------


def _make_options_flow(hass, *, current_url=BASE_URL, current_model=PROFILE_2X4HD):
    mock_entry = MagicMock()
    mock_entry.options = {}
    mock_entry.data = {CONF_URL: current_url, CONF_MODEL: current_model}
    flow = MiniDSPOptionsFlow(mock_entry)
    flow.hass = hass
    return flow


async def test_options_flow_shows_form_with_current_values(hass):
    flow = _make_options_flow(hass)
    result = await flow.async_step_init(None)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    schema = result["data_schema"].schema
    url_key = next(k for k in schema if str(k) == CONF_URL)
    assert url_key.default() == BASE_URL


async def test_options_flow_creates_entry(hass):
    flow = _make_options_flow(hass)
    new_url = "http://192.168.1.5:5380"
    result = await flow.async_step_init(
        {CONF_URL: new_url, CONF_MODEL: PROFILE_GENERIC}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_URL] == new_url
    assert result["data"][CONF_MODEL] == PROFILE_GENERIC


async def test_options_flow_uses_options_over_data(hass):
    """Options values take priority over data values when pre-populating form."""
    mock_entry = MagicMock()
    mock_entry.options = {CONF_URL: "http://options-url:5380", CONF_MODEL: PROFILE_GENERIC}
    mock_entry.data = {CONF_URL: BASE_URL, CONF_MODEL: PROFILE_2X4HD}
    flow = MiniDSPOptionsFlow(mock_entry)
    flow.hass = hass
    result = await flow.async_step_init(None)
    schema = result["data_schema"].schema
    url_key = next(k for k in schema if str(k) == CONF_URL)
    assert url_key.default() == "http://options-url:5380"
