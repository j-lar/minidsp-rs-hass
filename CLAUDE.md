# CLAUDE.md - Project Guide for minidsp-rs-hass

## Project Overview

Home Assistant custom integration for MiniDSP audio processors via the **minidsp-rs** HTTP/WebSocket daemon. Provides real-time volume, mute, source, preset, Dirac Live, and per-output gain control through Home Assistant entities.

- **Domain**: `minidsp`
- **IoT Class**: `local_push` (WebSocket-based real-time updates)
- **Min HA Version**: 2024.8
- **External Dependencies**: None (uses HA-provided aiohttp)

## Repository Structure

```
custom_components/minidsp-rs/
  __init__.py       # Integration lifecycle: setup, unload, reload, config listener
  api.py            # Async HTTP + WebSocket client wrapping minidsp-rs daemon
  coordinator.py    # DataUpdateCoordinator: polling + WebSocket level merging
  config_flow.py    # ConfigFlow (initial setup) + OptionsFlow (runtime changes)
  const.py          # Constants, device profiles (2x4HD, Generic), mapping helpers
  media_player.py   # MediaPlayer entity: volume, mute, source, preset (sound mode)
  sensor.py         # Level sensors (input/output dBFS) + diagnostic profile sensor
  switch.py         # Dirac Live + Mute toggle switches
  number.py         # Per-output gain sliders (-127 to +12 dB)
  select.py         # Preset + Source dropdown selectors
  manifest.json     # HA integration metadata
  openapi.json      # minidsp-rs API specification (OpenAPI 3.0)
```

## Architecture

```
Home Assistant UI
       |
Entity Platforms (media_player, sensor, switch, number, select)
       |
CoordinatorEntity (shared state subscription)
       |
MiniDSPCoordinator (DataUpdateCoordinator)
  - HTTP polling for initial/full state
  - WebSocket subscription for incremental level updates
       |
MiniDSPAPI (aiohttp HTTP client + WebSocket listener)
       |
minidsp-rs daemon (external process, HTTP + WS on same port)
```

**Data flow**:
1. Initial state via `GET /devices/{index}`
2. Real-time levels via WebSocket at `/devices/{index}?levels=true&poll=true`
3. Commands via `POST /devices/{index}/config` with JSON payload
4. After each command, `async_request_refresh()` fetches updated state

## Key Patterns

- All entities extend `CoordinatorEntity[MiniDSPCoordinator]` for automatic state updates
- Device profiles in `const.py` define available sources and preset count per model
- `build_source_maps()` / `build_preset_maps()` create bidirectional label-to-API mappings
- Volume is stored as dB (-127 to 0) internally; media_player converts to 0.0-1.0 level
- WebSocket reconnects with exponential backoff (1s to 60s cap)
- Level values are rounded to integers throughout (coordinator + sensors)
- URL scheme auto-conversion: http->ws, https->wss, tcp->ws for WebSocket connections

## Device Profiles

- **2x4HD**: Analog, USB, TOSLINK sources; 4 presets
- **Generic/Basic**: Full source enum (Analog, Toslink, Spdif, Usb, Aesebu, Rca, Xlr, Lan, I2S); 4 presets
- Auto-detection via product name substring matching from `/devices` endpoint

## Development Notes

- No external Python dependencies; only HA-provided `aiohttp` and `voluptuous`
- No test suite currently exists
- No CI/CD pipeline configured
- All network I/O is async (aiohttp)
- Config flow uses `base_url` as unique_id to prevent duplicate entries
- `SCAN_INTERVAL_SECONDS = 1` is defined but `update_interval=None` is used (WebSocket-driven)
- Entities access the API via `coordinator._api` (private attribute access)
- `type: ignore[override]` comments are used on property overrides throughout

## Common Tasks

- **Add a new entity platform**: Create `<platform>.py`, add platform name to `PLATFORMS` in `__init__.py`, implement `async_setup_entry()` with coordinator lookup pattern
- **Add a new device profile**: Add entry to `DEVICE_PROFILES` in `const.py`, optionally add auto-detection key to `PRODUCT_NAME_MODEL_MAP`
- **Add a new API command**: Add convenience method to `MiniDSPAPI` in `api.py` wrapping `async_post_config()`
