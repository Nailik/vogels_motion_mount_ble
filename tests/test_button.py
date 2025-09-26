import pytest
from syrupy.assertion import SnapshotAssertion
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from unittest.mock import patch
from unittest.mock import MagicMock


from . import setup_integration

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from custom_components.vogels_motion_mount_ble.data import VogelsMotionMountPresetData

from custom_components.vogels_motion_mount_ble.button import (
    StartCalibrationButton,
    RefreshDataButton,
    DisconnectButton,
    SelectPresetDefaultButton,
    SelectPresetButton,
    DeletePresetButton,
    AddPresetButton,
)


async def test_all_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test all entities."""
    with patch(
        "custom_components.vogels_motion_mount_ble.PLATFORMS", [Platform.BUTTON]
    ):
        await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_start_calibration_button(mock_coord: MagicMock):
    button = StartCalibrationButton(mock_coord)
    await button.async_press()
    mock_coord.start_calibration.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_data_button(mock_coord: MagicMock):
    button = RefreshDataButton(mock_coord)
    await button.async_press()
    mock_coord.refresh_data.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_button(mock_coord: MagicMock):
    button = DisconnectButton(mock_coord)
    await button.async_press()
    mock_coord.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_select_preset_default_button(mock_coord: MagicMock):
    button = SelectPresetDefaultButton(mock_coord)
    await button.async_press()
    mock_coord.select_preset.assert_awaited_once_with(0)


@pytest.mark.asyncio
async def test_select_preset_button(mock_coord: MagicMock):
    button = SelectPresetButton(mock_coord, preset_index=1)
    await button.async_press()
    mock_coord.select_preset.assert_awaited_once_with(2)  # offset by +1


@pytest.mark.asyncio
async def test_delete_preset_button(mock_coord: MagicMock):
    button = DeletePresetButton(mock_coord, preset_index=1)
    await button.async_press()
    mock_coord.set_preset.assert_awaited_once()
    # Should replace preset with None data


@pytest.mark.asyncio
async def test_add_preset_button(mock_coord: MagicMock):
    button = AddPresetButton(mock_coord, preset_index=1)
    await button.async_press()
    mock_coord.set_preset.assert_awaited_once()
    called_arg = mock_coord.set_preset.await_args[0][0]
    assert isinstance(called_arg.data, VogelsMotionMountPresetData)
    assert called_arg.data.name == "1"
    assert called_arg.data.distance == 0
    assert called_arg.data.rotation == 0
