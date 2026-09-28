"""Holds the data that is stored in memory by the Vogels Motion Mount Integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VogelsMotionMountPinSettings(Enum):
    """Which pins the mount currently has set.

    The low two bits say which one exists: bit 0 the authorised user's, bit 1
    the supervisor's. Leaving out a combination is not a cosmetic gap — the
    value is read on every update, so a mount in a mode with no member here
    fails the whole fetch with "14 is not a valid VogelsMotionMountPinSettings"
    and every entity goes unavailable. 14 is reached by opening control to
    everyone while keeping settings for the supervisor.
    """

    Deactivated = 12
    Single = 13
    Supervisor = 14
    Multi = 15

    @property
    def authorised_user_pin_set(self) -> bool:
        """Whether operating the mount needs a pin."""
        return bool(self.value & 1)

    @property
    def supervisor_pin_set(self) -> bool:
        """Whether changing settings needs the supervisor's pin."""
        return bool(self.value & 2)


class VogelsMotionMountAuthenticationType(Enum):
    """Current authentication status."""

    Wrong = 0
    Control = 1
    Full = 2


class VogelsMotionMountAutoMoveType(Enum):
    """Authentication options."""

    Hdmi_1_On = 0
    Hdmi_1_Off = 1
    Hdmi_2_On = 4
    Hdmi_2_Off = 5
    Hdmi_3_On = 8
    Hdmi_3_Off = 9
    Hdmi_4_On = 12
    Hdmi_4_Off = 13
    Hdmi_5_On = 16
    Hdmi_5_Off = 17


@dataclass
class VogelsMotionMountAuthenticationStatus:
    """Current authentication status."""

    auth_type: VogelsMotionMountAuthenticationType
    cooldown: int | None = None


@dataclass
class VogelsMotionMountPreset:
    """Preset data."""

    index: int
    data: VogelsMotionMountPresetData | None


@dataclass
class VogelsMotionMountPresetData:
    """Preset data."""

    distance: int
    name: str
    rotation: int


@dataclass
class VogelsMotionMountMultiPinFeatures:
    """Current set of features for authorised user."""

    change_default_position: bool
    change_name: bool
    change_presets: bool
    change_tv_on_off_detection: bool
    disable_channel: bool
    start_calibration: bool


@dataclass
class VogelsMotionMountVersions:
    """Version data."""

    ceb_bl_version: str
    mcp_bl_version: str
    mcp_fw_version: str
    mcp_hw_version: str


@dataclass
class VogelsMotionMountData:
    """Holds the data of the device."""

    automove: VogelsMotionMountAutoMoveType
    available: bool
    connected: bool
    distance: int
    freeze_preset_index: int
    multi_pin_features: VogelsMotionMountMultiPinFeatures
    name: str
    pin_setting: VogelsMotionMountPinSettings
    presets: list[VogelsMotionMountPreset]
    rotation: int
    tv_width: int
    versions: VogelsMotionMountVersions
    permissions: VogelsMotionMountPermissions
    requested_distance: int | None = None
    requested_rotation: int | None = None


@dataclass
class VogelsMotionMountPermissions:
    """Permissions for currently used pin."""

    auth_status: VogelsMotionMountAuthenticationStatus
    change_settings: bool
    change_default_position: bool
    change_name: bool
    change_presets: bool
    change_tv_on_off_detection: bool
    disable_channel: bool
    start_calibration: bool
