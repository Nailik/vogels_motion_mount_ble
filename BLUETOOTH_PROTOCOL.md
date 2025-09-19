# Bluetooth GATT Services and Characteristics

---

Encoding is usually Big Endian, noted when otherwise.

## Service 1: `3e6fe65d-ed78-11e4-895e-00026fd5c52c`

| UUID | Read | Write | Notify | Data |
|------|------|-------|--------|-------------|
| `c005fa00-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Movement (forward/backward), range: `0` - `100` |
| `c005fa01-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Rotation (left/right), range `-100` - `100` |
| `c005fa02-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Auto Move HDMI:<br>• 1: off `1` / on `00`<br>• 2: off `5` / on `4`<br>• 3: off `9` / on `8`<br>• 4: off `13` / on `12`<br>• 5: off `17` / on `16` |
| `c005fa03-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Calibration `1` to start calibration, returns increasing numbers until it ends with `0`, notify doesn't sent data |
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
