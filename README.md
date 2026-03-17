# Homeassistant MiniDSP

needs minidsp rs instance with http server

to configure, you need to prefix your MiniDSP-RS Host with `ws://`, for example `ws://192.168.2.151`

## Device profiles

Default profile targets the **miniDSP 2x4HD** (sources: Analog, USB, TOSLINK; 4 presets).
You can switch to **Generic/Basic** in the integration options to expose the full minidsp-rs
source enum for experimentation with other devices.
If no model is set, the integration attempts to auto-detect the device model from `/devices`.

## Lovelace Dashboard

A ready-made Lovelace dashboard YAML is provided at [`lovelace/minidsp-dashboard.yaml`](lovelace/minidsp-dashboard.yaml).

It covers all integration entities: main controls (volume, mute, source, preset), real-time input/output level gauges, per-channel gain/delay/mute, compressor controls, and diagnostics.

To use it, open your dashboard's raw YAML editor and paste the file contents, then replace every `YOUR_DEVICE_NAME` with your device's entity slug (find it in **Developer Tools → States**).

## Entities

- Media Player: volume, mute, source, preset
- Select: Preset
- Select: Source
- Switch: Mute
- Switch: Dirac Live
- Sensor (diagnostic): Device Profile
