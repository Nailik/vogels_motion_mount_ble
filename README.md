# Vogels MotionMount (BLE) for Home Assistant - Alpha

Project is still in Alpha, some features are missing and there are no unit tests yet.

## Setup

Use HACS to add this repository or copy the contents in the custom_integrations folder.

During Setup the following options appear:
- MAC: The mac address of the device, required to connect to a BLE device
- Device name: Local device name, only used within Home Assistant, not necessary to match the BLE Device name.
- PIN: Within the Vogel's MotionMount you can setup 2 different pins
  - Authorized user pin: this pin can be used to control the device or change settings
  - Supervisior pin: when this secondary pin is setup, the authorized user will loose the possibility to change the settings, which settings an authorized user has access to can be changed
- Preset Subdevices: This combines the actions of subdevices add/delete/name/distance/rotation/select into a secondary device

When the integration is setup the integration tries to connect to the Vogel's MotionMount on each restart, it tries in 1 minute intervals until successful connection.

## Limitations

- Preset Subdevices cannot be changed in options flow (doesn't work currently)
- Changing Pin is not supported yet
- Changing the name of a preset doesn't update it's entities yet, you need to restart Home Assistant

## Status

| Property | Description | Service | Supported | Note |
|----------|-------------|---------|------------|-|
| Name | Device Name | set_name | ✅ | Length 1-20 characters |
| Distance | Distance from Wall in Percentage | set_distance | ✅ |  |
| Rotation | Rotation left/right (get, set) | set_rotation | ✅ |  |
| Presets | Name | set_preset_name | ✅ | Length 1-20 characters (max length to be verified) | 
| Presets | Distance | set_preset_distance | ✅ |  | 
| Presets | Rotation | set_preset_rotation | ✅ |  | 
| Presets | Delete | delete_preset | ✅ | deletes a preset | 
| Presets | Add | add_preset | ✅ | adds a new preset | 
| Select Preset | Move TV to a preset | select_preset | ✅ |  |
| Auto Move | Auto Move to Freeze Position, On/Off and 5 different HDMI detection Modes | set_automove | ✅ | "off", "hdmi_1", "hdmi_2", "hdmi_3", "hdmi_4", "hdmi_5" |
| Freeze preset | Preset to be used when TV is turned of | set_freeze_preset | ✅ |  |
| TV width | Set the width of the TV in cm, in order for the Mount to know the max rotation | set_tv_width | ✅ |  |
| Authorized user Pin | Pin to controls or change the settings | | ✅ |  |
| Supervisor Pin | Pin to limit settings control for authorizes user | | ✅ |  |
| Authorizes user features | Wich settings an authorized user can change | | ❌ |  |
| CEB BL, FW Version | Version of CEB |  | ✅ |  |
| MCP BL, FW Version | Version of MCP |  | ✅ |  |

# Bluetooth GATT Services and Characteristics

---

Encoding is usually Big Endian, noted when otherwise.

## Service 1: `3e6fe65d-ed78-11e4-895e-00026fd5c52c`

| UUID | Read | Write | Notify | Data |
|------|------|-------|--------|-------------|
| `c005fa00-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Movement (forward/backward), range: `0` - `100` |
| `c005fa01-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Rotation (left/right), range `-100` - `100` |
| `c005fa02-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Auto Move HDMI:<br>• 1: off `1` / on `00`<br>• 2: off `5` / on `4`<br>• 3: off `9` / on `8`<br>• 4: off `13` / on `12`<br>• 5: off `17` / on `16` |
| `c005fa03-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa07-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa08-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | CEB BL Version |
| `c005fa09-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa0a-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 0 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa0b-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 1 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa0c-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 2 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa0d-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 3 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa0e-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 4 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa0f-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 5 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa10-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 6 Format:<br>• Byte 0: exists/deleted `1`/`0`<br>• Bytes 1–2: Distance<br>• Bytes 3–4: Rotation<br>• Bytes 5–20: Name (UTF-8 string) |
| `c005fa14-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Freeze position, single byte that defines which preset index is used |
| `c005fa15-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa16-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa17-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 0 (17 Bytes) |
| `c005fa18-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 1 (17 Bytes) |
| `c005fa19-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 2 (17 Bytes) |
| `c005fa1a-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 3 (17 Bytes) |
| `c005fa1b-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 4 (17 Bytes) |
| `c005fa1c-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 5 (17 Bytes) |
| `c005fa1d-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Additional Name (UTF-8 string) for Preset 6 (17 Bytes) |
| `c005fa21-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Unknown |
| `c005fa22-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa23-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa24-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Unknown |

---

## Service 2: `030013ac-4202-2d8e-ea11-3959c46ca10e`

| UUID | Read | Write | Notify | Data |
|------|------|-------|--------|-------------|
| `c005fa05-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Unknown |
| `c005fa06-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa25-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa26-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa28-0651-4800-b000-000000000000` | ✅ | ❌ | ✅ | Unknown |
| `c005fa29-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa2a-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Call Preset with id 0x00 - 0x06 |
| `c005fa2b-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | TV width in cm |
| `c005fa2d-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Authenticate for session, Little Endian format, authorised user pin is sent as is, for supervisior pin the high byte is offset by 64 |
| `c005fa2e-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Check permission:<br>• Settings and Control (supervisior): `128,128`<br>• Control only: `128,0` |
| `c005fa2f-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | change PIN, Little Endian  |
| `c005fa30-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa31-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Multi Pin features encoded as bitwise or. <br>0: change preset<br>1: change name<br>2: disable channel<br>3: change tv on off detection<br>4: change default position<br>5: start calibration  |
| `c005fa32-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa33-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Unknown |
| `c005fa34-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | MCP HW Version (Bytes 0-3), MCP BL Version (Bytes 3-5),  CEB FW Version (Bytes 5-7) |
| `c005fa35-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa36-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa37-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Name, exactly 20 bytes |
| `c005fa38-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa39-0651-4800-b000-000000000000` | ✅ | ❌ | ✅ | Pin Information<br>• No Pin: `12`<br>• Only Authorised user Pin: `13`• Different Pin for Authorised user and supervisior: `15` |
| `c005fa3a-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |

---

