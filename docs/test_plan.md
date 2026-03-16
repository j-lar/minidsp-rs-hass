# MiniDSP Integration — Manual Test Plan

This document describes end-to-end manual testing of the MiniDSP Home Assistant
integration against a real minidsp-rs daemon and hardware device.

**Reference docs**:
- minidsp-rs: https://minidsp-rs.pages.dev/getting-started
- Home Assistant developer docs: https://developers.home-assistant.io/

---

## Prerequisites

- [ ] MiniDSP hardware connected (e.g. 2x4 HD)
- [ ] minidsp-rs daemon running and accessible, e.g.:
  ```
  minidsp server --http 5380
  ```
  Or via the pre-built Docker image. Verify with:
  ```
  curl http://localhost:5380/devices
  ```
- [ ] Home Assistant dev instance running (e.g. via `hass -c config/`)
- [ ] Integration copied to `<ha_config>/custom_components/minidsp/`
  (rename the `minidsp-rs` directory to match the domain `minidsp`)
- [ ] Browser developer console open to watch for JavaScript errors
- [ ] HA log level set to DEBUG for the domain:
  ```yaml
  # configuration.yaml
  logger:
    default: warning
    logs:
      custom_components.minidsp: debug
  ```

---

## 1. Installation & Config Flow

| # | Step | Expected |
|---|------|----------|
| 1.1 | Open **Settings → Devices & Services → Add Integration**, search "MiniDSP" | Integration card appears |
| 1.2 | Enter daemon URL (e.g. `http://localhost:5380`), leave model as "2x4HD", click Submit | Entry created, no errors in logs |
| 1.3 | Check HA logs for `[minidsp]` messages | No errors or warnings during setup |
| 1.4 | Check **Settings → Devices & Services → MiniDSP** | Device listed, entities visible |

---

## 2. Device Registry

| # | Step | Expected |
|---|------|----------|
| 2.1 | Navigate to the MiniDSP device in **Settings → Devices** | Device shows **Manufacturer: MiniDSP** |
| 2.2 | Check **Model** field | Shows product name (e.g. "2x4 HD") or profile name |

---

## 3. Entity Inventory

Confirm all expected entities are created after setup:

| Entity type | Expected entities |
|-------------|-------------------|
| Media Player | 1× MiniDSP (volume, mute, source, sound mode) |
| Sensor | 1× Device Profile (diagnostic); Input Level 1–N; Output Level 1–N |
| Switch | Dirac Live; Mute |
| Number | Output 1 Gain … Output N Gain (one per output channel) |
| Select | Preset; Source |

- [ ] All entities listed above appear in HA

---

## 4. Volume Control

| # | Step | Expected |
|---|------|----------|
| 4.1 | Use the Media Player card slider to set volume to 50% | Device volume changes; `minidsp status` shows approx −63.5 dB |
| 4.2 | Use Developer Tools → Services → `media_player.volume_up` | Volume increases by one step |
| 4.3 | Set volume to 0% | Device volume goes to −127 dB (minimum) |
| 4.4 | Set volume to 100% | Device volume goes to 0 dB |

---

## 5. Mute

| # | Step | Expected |
|---|------|----------|
| 5.1 | Toggle **Mute** switch ON | Audio muted on device; Media Player mute indicator active |
| 5.2 | Toggle **Mute** switch OFF | Audio resumes |
| 5.3 | Use Media Player mute button | Both Mute switch and Media Player show same state |
| 5.4 | Verify both Mute switch and Media Player are in sync | States match without page refresh |

---

## 6. Source Selection

| # | Step | Expected |
|---|------|----------|
| 6.1 | Change source via **Source** select entity | Device input changes; Media Player source updates |
| 6.2 | Change source via Media Player source selector | Source select entity updates to match |
| 6.3 | Cycle through all available sources | Each source is selectable, no errors |

---

## 7. Preset Selection

| # | Step | Expected |
|---|------|----------|
| 7.1 | Select "Preset 2" via the **Preset** select entity | Device switches to preset 2 |
| 7.2 | Change preset via Media Player sound mode selector | Preset select entity updates to match |
| 7.3 | Switch back to "Preset 1" | Confirmed on device |

---

## 8. Dirac Live

| # | Step | Expected |
|---|------|----------|
| 8.1 | Toggle **Dirac Live** switch ON | Dirac Live activated on device |
| 8.2 | Toggle **Dirac Live** switch OFF | Dirac Live deactivated |
| 8.3 | Check `extra_state_attributes` of Media Player | `dirac` attribute reflects current state |

---

## 9. Output Gains

| # | Step | Expected |
|---|------|----------|
| 9.1 | Set **Output 1 Gain** to −6 dB | Per-channel output gain changes on device |
| 9.2 | Set **Output 2 Gain** to 0 dB | Confirmed |
| 9.3 | Try to set a gain outside −127 to +12 dB | HA should reject (outside slider range) |

---

## 10. Level Sensors (Real-Time)

| # | Step | Expected |
|---|------|----------|
| 10.1 | Play audio through the MiniDSP | Input Level sensors show non-zero dBFS values |
| 10.2 | Watch sensors update in real-time | Values change as audio level changes (WebSocket-driven) |
| 10.3 | Stop audio | Sensors return to −∞ / low values |
| 10.4 | Verify units | Sensor shows "dBFS" unit |

---

## 11. WebSocket Reconnect

| # | Step | Expected |
|---|------|----------|
| 11.1 | Stop the minidsp-rs daemon process | HA logs show WebSocket disconnect warning |
| 11.2 | Wait 30+ seconds (through full backoff cycle) | No HA crash or error storm; entities remain available |
| 11.3 | Restart minidsp-rs daemon | HA logs show successful reconnect |
| 11.4 | Change volume on device externally | After reconnect, HA entities refresh to reflect device state |

---

## 12. Options Flow

| # | Step | Expected |
|---|------|----------|
| 12.1 | Go to **Settings → Devices & Services → MiniDSP → Configure** | Options form opens with current URL and model |
| 12.2 | Change the URL to a different address, click Submit | Integration reloads with new URL |
| 12.3 | Change the model to "Generic/Basic" | Source list updates to show all available sources |

---

## 13. Reload & Restart

| # | Step | Expected |
|---|------|----------|
| 13.1 | Reload the integration via **⋮ → Reload** | Entities re-appear, no duplicate device entries |
| 13.2 | Restart Home Assistant | Integration loads cleanly on startup |

---

## Pass Criteria

All items above checked with no unexpected errors in logs or UI.
