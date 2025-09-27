"""Tests for number entities."""

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.vogels_motion_mount_ble.coordinator import (
    VogelsMotionMountBleCoordinator,
)
from custom_components.vogels_motion_mount_ble.data import (
    VogelsMotionMountPreset,
    VogelsMotionMountPresetData,
)
from custom_components.vogels_motion_mount_ble.number import (
    DistanceNumber,
    PresetDistanceNumber,
    PresetRotationNumber,
    RotationNumber,
    TVWidthNumber,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import setup_integration  # noqa: TID251

# -------------------------------
# region Setup
# -------------------------------


async def test_all_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test all entities."""
    with patch(
        "custom_components.vogels_motion_mount_ble.PLATFORMS", [Platform.NUMBER]
    ):
        await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


# -------------------------------
# region Actions
# -------------------------------


@pytest.mark.asyncio
async def test_set_distance_number(mock_coord: VogelsMotionMountBleCoordinator):
    """Set distance number."""
    number = DistanceNumber(mock_coord)
    await number.async_set_native_value(42.7)
    mock_coord.request_distance.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_set_rotation_number(mock_coord: VogelsMotionMountBleCoordinator):
    """Set distance number."""
    number = RotationNumber(mock_coord)
    await number.async_set_native_value(-33.9)
    mock_coord.request_rotation.assert_awaited_once_with(-33)


@pytest.mark.asyncio
async def test_set_tv_width_number(mock_coord: VogelsMotionMountBleCoordinator):
    """Set tv width number."""
    number = TVWidthNumber(mock_coord)
    await number.async_set_native_value(123.4)
    mock_coord.set_tv_width.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_set_preset_distance_number(mock_coord: VogelsMotionMountBleCoordinator):
    """Set preset distance number."""
    # preset with existing data
    preset = VogelsMotionMountPreset(
        index=0,
        data=VogelsMotionMountPresetData(name="0", distance=10, rotation=20),
    )
    mock_coord.data.presets = [preset]

    number = PresetDistanceNumber(mock_coord, preset_index=0)
    await number.async_set_native_value(55.6)

    mock_coord.set_preset.assert_awaited_once()
    called_arg = mock_coord.set_preset.await_args[0][0]
    assert isinstance(called_arg, VogelsMotionMountPreset)
    assert called_arg.data.distance == 55


@pytest.mark.asyncio
async def test_set_preset_distance_number_without_data(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Set preset distance number."""
    # preset without data
    preset = VogelsMotionMountPreset(index=0, data=None)
    mock_coord.data.presets = [preset]

    number = PresetDistanceNumber(mock_coord, preset_index=0)
    await number.async_set_native_value(33.3)

    mock_coord.set_preset.assert_awaited_once()
    called_arg = mock_coord.set_preset.await_args[0][0]
    assert called_arg.data.distance == 33
    assert called_arg.data.name == "0"


@pytest.mark.asyncio
async def test_set_preset_rotation_number(mock_coord: VogelsMotionMountBleCoordinator):
    """Set preset rotation number."""
    preset = VogelsMotionMountPreset(
        index=1,
        data=VogelsMotionMountPresetData(name="1", distance=15, rotation=-10),
    )
    mock_coord.data.presets = [preset]

    number = PresetRotationNumber(mock_coord, preset_index=0)
    await number.async_set_native_value(77.9)

    mock_coord.set_preset.assert_awaited_once()
    called_arg = mock_coord.set_preset.await_args[0][0]
    assert called_arg.data.rotation == 77


@pytest.mark.asyncio
async def test_set_preset_rotation_number_without_data(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Set preset rotation number."""
    preset = VogelsMotionMountPreset(index=0, data=None)
    mock_coord.data.presets = [preset]

    number = PresetRotationNumber(mock_coord, preset_index=0)
    await number.async_set_native_value(-45.2)

    mock_coord.set_preset.assert_awaited_once()
    called_arg = mock_coord.set_preset.await_args[0][0]
    assert called_arg.data.rotation == -45
    assert called_arg.data.name == "0"


# -------------------------------
# region Value Logic
# -------------------------------


def test_distance_number_native_value_no_data(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test distance no data."""
    mock_coord.data = None
    number = DistanceNumber(mock_coord)
    assert number.native_value is None


def test_distance_number_native_value_requested(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Request distance."""
    mock_coord.data.requested_distance = 42
    mock_coord.data.distance = 99  # should be ignored if requested_distance exists
    number = DistanceNumber(mock_coord)
    assert number.native_value == 42


def test_distance_number_native_value_fallback(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Fallback to current distance if no distance was requested."""
    mock_coord.data.requested_distance = None
    mock_coord.data.distance = 77
    number = DistanceNumber(mock_coord)
    assert number.native_value == 77


def test_rotation_number_native_value_no_data(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test rotation no data."""
    mock_coord.data = None
    number = RotationNumber(mock_coord)
    assert number.native_value is None


def test_rotation_number_native_value_requested(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Request rotation."""
    mock_coord.data.requested_rotation = -33
    mock_coord.data.rotation = 88  # should be ignored if requested_rotation exists
    number = RotationNumber(mock_coord)
    assert number.native_value == -33


def test_rotation_number_native_value_fallback(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Fallback to current rotation if no rotation was requested."""
    mock_coord.data.requested_rotation = None
    mock_coord.data.rotation = 55
    number = RotationNumber(mock_coord)
    assert number.native_value == 55


def test_preset_distance_number_native_value_none(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test preset distance no data."""
    # Preset with no data
    preset = VogelsMotionMountPreset(index=0, data=None)
    mock_coord.data.presets = [preset]
    number = PresetDistanceNumber(mock_coord, preset_index=0)
    assert number.native_value is None


def test_preset_distance_number_native_value_with_data(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test preset distance."""
    # Preset with data
    preset = VogelsMotionMountPreset(
        index=0, data=VogelsMotionMountPresetData(name="test", distance=42, rotation=0)
    )
    mock_coord.data.presets = [preset]
    number = PresetDistanceNumber(mock_coord, preset_index=0)
    assert number.native_value == 42


def test_preset_rotation_number_native_value_none(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test preset rotation no data."""
    # Preset with no data
    preset = VogelsMotionMountPreset(index=0, data=None)
    mock_coord.data.presets = [preset]
    number = PresetRotationNumber(mock_coord, preset_index=0)
    assert number.native_value is None


def test_preset_rotation_number_native_value_with_data(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test preset rotation."""
    # Preset with data
    preset = VogelsMotionMountPreset(
        index=0, data=VogelsMotionMountPresetData(name="test", distance=0, rotation=-15)
    )
    mock_coord.data.presets = [preset]
    number = PresetRotationNumber(mock_coord, preset_index=0)
    assert number.native_value == -15
