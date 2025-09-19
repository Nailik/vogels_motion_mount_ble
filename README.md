# Vogels MotionMount Bluetooth Home Assistant Integratioon

[![Open Vogels Motion Mount BLE in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Nailik&repository=vogels_motion_mount_ble&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/github/v/release/Nailik/vogels_motion_mount_ble)](https://github.com/Nailik/vogels_motion_mount_ble/releases/latest)
![Downloads latest](https://img.shields.io/github/downloads/nailik/vogels_motion_mount_ble/latest/total.svg)
![Downloads](https://img.shields.io/github/downloads/nailik/vogels_motion_mount_ble/total)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Home Assistant integration allows to control the Vogel's MotionMount (TVM 7675) over Bluetooth Low Energy (BLE).

---

## High-level description & use cases
This integration exposes the MotionMount as local devices and entities in Home Assistant so you can:
- Move the mount forward/backward and rotate left/right (percentage-based control).
- Call named presets and add/delete presets.
- Set a freeze preset used when the TV is turned off and how the TV status is detected.
- Change PIN for authorised user and supervisior including specific permissions.
- Start the calibration process.
- Read firmware/hardware version information.

Use cases:
- Move to a named preset when the TV turns on/off or based on another trigger.
- Automatically rotate or adjust distance based on other sensors or automations.
- Expose device status and firmware versions for inventory/monitoring.

---

## Supported device(s)
- [Vogel’s MotionMount TVM 7675](https://www.vogels.com/de-de/c/tvm-7675-elektrische-tv-wandhalterung-schwarz)
> PRO Version possibly works as well but was not tested

---

## Requirements & prerequisites

- Home Assistant **2025.6.0 or newer**  
- Bluetooth support on the host (integration depends on HA’s `bluetooth` integration)  
- Python package: **`bleak>=0.21.1`**

---

## Installation

### Recommended: HACS

1. Add this repository to HACS (Integrations → Custom repositories) or click the “Open in HACS” badge above.  
2. Install the integration from HACS → Integrations.  
3. Restart Home Assistant.

### Manual installation

1. Copy the `custom_components/vogels_motion_mount_ble` folder into `<config>/custom_components/`.  
2. Restart Home Assistant.  
3. Configure via **Settings → Devices & Services → Add integration → Vogels MotionMount (BLE)**.

---

## Setup

During setup, the integration asks for:

- **MAC** — the BLE MAC address of the device.  
- **Device name** — a friendly name for the device (optional).  
- **PIN** — PIN to be used, can be changed later
  - *Authorised user PIN*: can control the device or change settings.  
  - *Supervisor PIN*: allows additional control and restrictions.

- The integration can **automatically detect the Mount via Bluetooth**.

> **Note**: Ensure your Bluetooth adapter is working and within range of the mount.

---
### Entities

#### Binary Sensors

- **Connected**  
  - **Description**: Indicates whether the MotionMount device is currently connected via Bluetooth.

#### Buttons

- **Start Calibration**  
  - **Description**: Starts the calibration process for the mount.

- **Refresh Data**  
  - **Description**: Read current data from the mount.

- **Disconnect**  
  - **Description**: Disconnects the mount from Home Assistant.

- **Select default preset**  
  - **Description**: Homes the mount into the default position.

- **Add Preset**  
  - **Description**: Adds preset at the specific index.

- **Delete Preset**  
  - **Description**: Deletes a stored preset from the mount.

- **Select Preset**  
  - **Description**: Moves the mount to a stored preset.

#### Numbers

- **Distance**  
  - **Description**: Distance of the mount from the wall.  
  - **Range**: 0 to 100  
  - **Step**: 1

- **Rotation**  
  - **Description**: Rotation angle of the mount.  
  - **Range**: -100 to 100  
  - **Step**: 1

- **TV Width**  
  - **Description**: Width of the TV in centimeters.  
  - **Maximum**: 243  
  - **Step**: 1

- **Preset Distance**  
  - **Description**: Distance for each preset.  
  - **Range**: 0 to 100  
  - **Step**: 1

- **Preset Rotation**  
  - **Description**: Rotation angle for each preset.  
  - **Range**: -100 to 100  
  - **Step**: 1

#### Selects

- **Automove**  
  - **Description**: Configures automove based on HDMI input.  
  - **Options**: `"off"`, `"hdmi_1"`, `"hdmi_2"`, `"hdmi_3"`, `"hdmi_4"`, `"hdmi_5"`

- **Freeze**  
  - **Description**: Sets the preset to move to when automove is triggered.
  - **Options**: `"0"` (default wall), `"1"`–`"7"` (custom presets)

#### Sensors

- **Distance**  
  - **Description**: Current distance of the mount from the wall.  
  - **Range**: 0 to 100  

- **Rotation**  
  - **Description**: Current rotation of the mount.  
  - **Range**: -100 to 100  

- **Firmware Version**  
  - **Description**: Current firmware version

- **Hardware Version**  
  - **Description**: Hardware version

#### Switches

- **Multi-PIN Features**  
  - **Description**: Enables or disables multi-PIN feature access.  
  - **Note**: Only works if both authorised user and supervisor PINs are set up.

#### Texts

- **Name**  
  - **Description**: Mount name (max 32 characters)

- **Preset Name**  
  - **Description**: Names for each preset (max 32 characters)

---

## Actions

---

### Action: Set authorised user PIN

The `vogels_motion_mount_ble.set_authorised_user_pin` service sets the authorised user PIN.
Authorised users are allowed to control and change the settings (if there is a supervisior a subset of allowed settings can be configured).

- **Data attributes**:
  - `device_id` — Required
  - `pin` — string, Required
    - **Constraints**: Must be exactly 4 digits, 0000 removes the pin (removing only available if no supervisior is set up)
  - **Example**: `{"device_id": "12345", "pin": "1234"}`


---

### Action: Set supervisor PIN

The `vogels_motion_mount_ble.set_supervisor_pin` service sets the supervisor PIN.
If set downgrades authorised user to control only, a subset of features can be allowed to be changed by an authorised user.

- **Data attributes**:
  - `device_id` — Required
  - `pin` — string, Required
    - **Constraints**: Must be exactly 4 digits, 0000 removes the pin (setting pin only available if an authorised user is set up)
  - **Example**: `{"device_id": "12345", "pin": "5678"}`
  
---

## Example

This example shows how to automatically move the Motion Mount to a preset when the user wants to eat.

```yaml
alias: Move Motion Mount to Dining Room for Meals
description: "Automatically move the Motion Mount to the Dining Room preset when the user wants to eat."
trigger:
  - platform: state
    entity_id: input_boolean.user_wants_to_eat
    to: 'on'
condition: []
action:
  - service: vogels_motion_mount_ble.select_preset
    data:
      device_id: YOUR_DEVICE_ID_HERE
      preset: "1"   # Preset 1 corresponds to "Dining Room"
mode: single

---

## Known limitations
The Vogles Motion Mount BLE integration currently has the following limitations:

The Mount will disconnect BLE automatically, therefore no permanent connection is possible.
Checking for updates is currently not supported.

---

## Troubleshooting

If you're experiencing issues with your Vogles Motion Mount BLE integration, try these general troubleshooting steps:

Make sure your Vogels Motion Mount is in range, is powered on and properly also the Bluetooth connection is turned on. Validate if your Bluetooth devices can find the Motion Mount via it's exposed discoveries.

It's possible to reset the Motion Mount by removing the cover and pressing on the reset it will blink fast. For any LED error codes check the manual.

---

## Removing the integration

This integration follows standard integration removal, no extra steps are required.