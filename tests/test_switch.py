"""Tests for switch entities."""

from dataclasses import replace
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
from custom_components.vogels_motion_mount_ble.switch import (
    MultiPinFeatureChangeDefaultPositionSwitch,
    MultiPinFeatureChangeNameSwitch,
    MultiPinFeatureChangePresetsSwitch,
    MultiPinFeatureChangeTvOnOffDetectionSwitch,
    MultiPinFeatureDisableChannelSwitch,
    MultiPinFeatureStartCalibrationSwitch,
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
        "custom_components.vogels_motion_mount_ble.PLATFORMS", [Platform.SWITCH]
    ):
        await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


# -------------------------------
# region Actions
# -------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("switch_cls", "field"),
    [
        (MultiPinFeatureChangePresetsSwitch, "change_presets"),
        (MultiPinFeatureChangeNameSwitch, "change_name"),
        (MultiPinFeatureDisableChannelSwitch, "disable_channel"),
        (MultiPinFeatureChangeTvOnOffDetectionSwitch, "change_tv_on_off_detection"),
        (MultiPinFeatureChangeDefaultPositionSwitch, "change_default_position"),
        (MultiPinFeatureStartCalibrationSwitch, "start_calibration"),
    ],
)
async def test_multi_pin_features_switch_toggle_actions(
    mock_coord: VogelsMotionMountBleCoordinator, switch_cls, field
):
    """Test all switch actions for multi pin features."""
    # Ensure initial field is False
    features = replace(mock_coord.data.multi_pin_features, **{field: False})
    mock_coord.data.multi_pin_features = features
    mock_coord.set_multi_pin_features = AsyncMock()

    entity = switch_cls(mock_coord)
    assert entity.is_on is False

    # Turn on → should toggle field True
    await entity.async_turn_on()
    called_features = mock_coord.set_multi_pin_features.await_args[0][0]
    assert getattr(called_features, field) is True

    mock_coord.set_multi_pin_features.reset_mock()

    # Update coordinator state → set field True
    mock_coord.data.multi_pin_features = replace(features, **{field: True})
    assert entity.is_on is True

    # Turn off → should toggle field False
    await entity.async_turn_off()
    called_features = mock_coord.set_multi_pin_features.await_args[0][0]
    assert getattr(called_features, field) is False
