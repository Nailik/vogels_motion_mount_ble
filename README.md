# Vogels MotionMount (BLE) for Home Assistant - DEV

## Installation

## Status

| Property | Description | Service | Supported |
| Name | Device Name (get, set) | set_name | ✅ |

# Bluetooth GATT Services and Characteristics

---

## Service 1: `3e6fe65d-ed78-11e4-895e-00026fd5c52c`

| UUID | Read | Write | Notify | Data |
|------|------|-------|--------|-------------|
| `c005fa00-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Movement (forward/backward), range: 0x0000 – 0x0064 |
| `c005fa01-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Rotation |
| `c005fa02-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Auto Move HDMI:<br>• 1: off `0x001` / on `0x000`<br>• 2: off `0x005` / on `0x004`<br>• 3: off `0x009` / on `0x008`<br>• 4: off `0x013` / on `0x012`<br>• 5: off `0x017` / on `0x016` |
| `c005fa03-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa07-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa08-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | CEB BL Version |
| `c005fa09-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa0a-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 0 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa0b-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 1 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa0c-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 2 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa0d-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 3 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa0e-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 4 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa0f-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 5 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa10-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Preset 6 Format:<br>• Bytes 1–2: LittleEndian, Distance<br>• Bytes 3–4: LittleEndian, Rotation<br>• Bytes 5–end: Name (UTF-8 string) |
| `c005fa14-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Freeze position |
| `c005fa15-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa16-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa17-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa18-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa19-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa1a-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa1b-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa1c-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa1d-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
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
| `c005fa2d-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Settings PIN to authenticate session |
| `c005fa2e-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Check if PIN is required:<br>• Not required: `0x80800000`<br>• Required: `0x00000000` |
| `c005fa2f-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Control PIN to authenticate session |
| `c005fa30-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa32-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Unknown |
| `c005fa33-0651-4800-b000-000000000000` | ❌ | ✅ | ❌ | Unknown |
| `c005fa34-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa35-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa36-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |
| `c005fa37-0651-4800-b000-000000000000` | ✅ | ✅ | ❌ | Name |
| `c005fa38-0651-4800-b000-000000000000` | ✅ | ❌ | ❌ | Unknown |
| `c005fa39-0651-4800-b000-000000000000` | ✅ | ❌ | ✅ | Unknown |
| `c005fa3a-0651-4800-b000-000000000000` | ✅ | ✅ | ✅ | Unknown |

---

