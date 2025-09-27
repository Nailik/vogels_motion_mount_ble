import pytest
from syrupy.assertion import SnapshotAssertion
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from unittest.mock import patch

from . import setup_integration

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from unittest.mock import AsyncMock
from custom_components.vogels_motion_mount_ble.data import VogelsMotionMountPresetData

from custom_components.vogels_motion_mount_ble.text import (
    NameText,
    PresetNameText,
)

# -------------------------------
# endregion
# region Setup
# -------------------------------


async def test_all_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test all entities."""
    with patch("custom_components.vogels_motion_mount_ble.PLATFORMS", [Platform.TEXT]):
        await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


# -------------------------------
# endregion
# region Actions
# -------------------------------


@pytest.mark.asyncio
async def test_name_text_set_value(mock_coord):
    mock_coord.set_name = AsyncMock()
    mock_coord.data.name = "Old Name"

    entity = NameText(mock_coord)

    # native_value reflects coordinator
    assert entity.native_value == "Old Name"

    # Set a new name
    await entity.async_set_value("New Name")
    mock_coord.set_name.assert_awaited_once_with("New Name")


@pytest.mark.asyncio
async def test_preset_name_text_set_value_existing_data(mock_coord):
    preset = mock_coord.data.presets[0]
    preset.data = VogelsMotionMountPresetData(
        name="Preset 1", distance=100, rotation=20
    )
    mock_coord.set_preset = AsyncMock()

    entity = PresetNameText(mock_coord, 0)

    # native_value reflects current preset name
    assert entity.native_value == "Preset 1"

    # Update name → should pass updated preset to coordinator
    await entity.async_set_value("New Preset Name")
    called_preset = mock_coord.set_preset.await_args[0][0]
    assert called_preset.data.name == "New Preset Name"


@pytest.mark.asyncio
async def test_preset_name_text_set_value_no_existing_data(mock_coord):
    preset = mock_coord.data.presets[1]
    preset.data = None
    mock_coord.set_preset = AsyncMock()

    entity = PresetNameText(mock_coord, 1)

    # native_value should be None if no data exists
    assert entity.native_value is None

    # Update name → should create a fresh preset data object
    await entity.async_set_value("Fresh Name")
    called_preset = mock_coord.set_preset.await_args[0][0]
    assert called_preset.data.name == "Fresh Name"
    assert called_preset.data.distance == 0
    assert called_preset.data.rotation == 0


# -------------------------------
# endregion
# -------------------------------
