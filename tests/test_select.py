"""Tests for select entities."""

from unittest.mock import AsyncMock, patch

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
    VogelsMotionMountAutoMoveType,
    VogelsMotionMountPreset,
    VogelsMotionMountPresetData,
)
from custom_components.vogels_motion_mount_ble.select import (
    AutomoveSelect,
    CurrentPresetSelect,
    FreezePresetSelect,
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
        "custom_components.vogels_motion_mount_ble.PLATFORMS", [Platform.SELECT]
    ):
        await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


# -------------------------------
# region Actions
# -------------------------------


@pytest.mark.asyncio
async def test_automove_select_option_zero(mock_coord: VogelsMotionMountBleCoordinator):
    """Test automove select option."""
    mock_coord.set_automove = AsyncMock()
    # Current automove → Hdmi_2_On (value=4)
    mock_coord.data.automove = VogelsMotionMountAutoMoveType.Hdmi_2_On
    select = AutomoveSelect(mock_coord)

    await select.async_select_option("0")

    # "0" means Off → should pick Hdmi_2_Off (value=5)
    mock_coord.set_automove.assert_awaited_once_with(
        VogelsMotionMountAutoMoveType.Hdmi_2_Off
    )


@pytest.mark.asyncio
async def test_automove_select_option_enabled(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test automove select option."""
    mock_coord.set_automove = AsyncMock()
    mock_coord.data.automove = VogelsMotionMountAutoMoveType.Hdmi_1_Off
    select = AutomoveSelect(mock_coord)

    await select.async_select_option("3")

    # "3" means Hdmi_3_On (value=8)
    mock_coord.set_automove.assert_awaited_once_with(
        VogelsMotionMountAutoMoveType.Hdmi_3_On
    )


@pytest.mark.asyncio
async def test_freeze_preset_select_option(mock_coord: VogelsMotionMountBleCoordinator):
    """Test freeze preset option."""
    mock_coord.set_freeze_preset = AsyncMock()
    # Build presets
    presets = [
        VogelsMotionMountPreset(
            0, VogelsMotionMountPresetData(name="one", distance=10, rotation=5)
        ),
        VogelsMotionMountPreset(
            1, VogelsMotionMountPresetData(name="two", distance=20, rotation=10)
        ),
    ]
    mock_coord.data.presets = presets
    select = FreezePresetSelect(mock_coord)

    # Options will be ["0", "one", "two"]
    await select.async_select_option("two")

    # "two" is index 2
    mock_coord.set_freeze_preset.assert_awaited_once_with(2)


# -------------------------------
# region Current option
# -------------------------------


def test_automove_select_current_option_off(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test automove off option."""
    # Off case: Hdmi_3_Off = 9 → odd → maps to "0"
    mock_coord.data.automove = VogelsMotionMountAutoMoveType.Hdmi_3_Off
    select = AutomoveSelect(mock_coord)
    assert select.current_option == "0"


def test_automove_select_current_option_on(mock_coord: VogelsMotionMountBleCoordinator):
    """Test automove on option."""
    # On case: Hdmi_4_On = 12 → even → maps to (12 // 4) + 1 = 4
    mock_coord.data.automove = VogelsMotionMountAutoMoveType.Hdmi_4_On
    select = AutomoveSelect(mock_coord)
    assert select.current_option == "4"


def test_freeze_preset_select_current_option_none_index(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test freeze preset no option."""
    mock_coord.data.freeze_preset_index = None
    mock_coord.data.presets = []
    select = FreezePresetSelect(mock_coord)
    assert select.current_option is None


def test_freeze_preset_select_current_option_invalid_index(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test freeze preset invalid index."""
    mock_coord.data.freeze_preset_index = 99  # out of range
    mock_coord.data.presets = []
    select = FreezePresetSelect(mock_coord)
    assert select.current_option is None


def test_freeze_preset_select_current_option_valid(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test freeze preset valid option."""
    presets = [
        VogelsMotionMountPreset(
            0, VogelsMotionMountPresetData(name="one", distance=10, rotation=5)
        ),
        VogelsMotionMountPreset(
            1, VogelsMotionMountPresetData(name="two", distance=20, rotation=10)
        ),
    ]
    mock_coord.data.presets = presets
    mock_coord.data.freeze_preset_index = 2  # corresponds to "two"
    select = FreezePresetSelect(mock_coord)

    # Options should be ["0", "one", "two"]
    assert select.current_option == "two"


# -------------------------------
# region Current preset
# -------------------------------


def _current_preset_select(
    mock_coord: VogelsMotionMountBleCoordinator, distance: int, rotation: int
) -> CurrentPresetSelect:
    mock_coord.data.presets = [
        VogelsMotionMountPreset(
            0, VogelsMotionMountPresetData(name="one", distance=50, rotation=20)
        ),
        VogelsMotionMountPreset(1, None),
        VogelsMotionMountPreset(
            2, VogelsMotionMountPresetData(name="two", distance=54, rotation=20)
        ),
        VogelsMotionMountPreset(
            3, VogelsMotionMountPresetData(name="one", distance=100, rotation=-100)
        ),
    ]
    mock_coord.data.distance = distance
    mock_coord.data.rotation = rotation
    return CurrentPresetSelect(mock_coord)


def test_current_preset_options(mock_coord: VogelsMotionMountBleCoordinator):
    """Test options skip missing presets and stay unique."""
    select = _current_preset_select(mock_coord, 0, 0)
    assert select.options == ["0", "one", "two", "one (4)"]


@pytest.mark.parametrize(
    ("distance", "rotation", "expected"),
    [
        (0, 0, "0"),
        (2, -3, "0"),
        (4, 0, None),
        (50, 20, "one"),
        (51, 17, "one"),
        (53, 20, "two"),
        (54, 24, None),
        (98, -97, "one (4)"),
        (75, 0, None),
    ],
)
def test_current_preset_current_option(
    mock_coord: VogelsMotionMountBleCoordinator,
    distance: int,
    rotation: int,
    expected: str | None,
):
    """Test current preset is detected within tolerance and closest match wins."""
    select = _current_preset_select(mock_coord, distance, rotation)
    assert select.current_option == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("option", "expected_index"),
    [("0", 0), ("one", 1), ("two", 3), ("one (4)", 4)],
)
async def test_current_preset_select_option(
    mock_coord: VogelsMotionMountBleCoordinator, option: str, expected_index: int
):
    """Test selecting a preset moves to the device preset index."""
    mock_coord.select_preset = AsyncMock()
    select = _current_preset_select(mock_coord, 0, 0)
    await select.async_select_option(option)
    mock_coord.select_preset.assert_awaited_once_with(expected_index)
