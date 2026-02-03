# Homeassistant MiniDSP

needs minidsp rs instance with http server

to configure, you need to prefix your MiniDSP-RS Host with `ws://`, for example `ws://192.168.2.151`

## Device profiles

Default profile targets the **miniDSP 2x4HD** (sources: Analog, USB, TOSLINK; 4 presets).
You can switch to **Generic/Basic** in the integration options to expose the full minidsp-rs
source enum for experimentation with other devices.
If no model is set, the integration attempts to auto-detect the device model from `/devices`.

## Entities

- Media Player: volume, mute, source, preset
- Select: Preset
- Select: Source
- Switch: Mute
- Switch: Dirac Live
- Sensor (diagnostic): Device Profile
