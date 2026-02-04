# Homeassistant MiniDSP

needs minidsp rs instance with http server

to configure, use the HTTP base URL (for example `http://192.168.2.151`).
`ws://` or `wss://` will be normalized to HTTP/HTTPS automatically.

## Device profiles

Default profile targets the **miniDSP 2x4HD** (sources: Analog, USB, TOSLINK; 4 presets).
You can switch to **Generic/Basic** in the integration options to expose the full minidsp-rs
source enum for experimentation with other devices.
If no model is set, the integration attempts to auto-detect the device model from `/devices`.
If you have multiple devices behind one daemon, set the **Device Index** option.

## Entities

- Media Player: volume, mute, source, preset
- Select: Preset
- Select: Source
- Switch: Mute
- Switch: Dirac Live
- Sensor (diagnostic): Device Profile
- Binary Sensor (diagnostic): Connected
