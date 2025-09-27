"""Tests for sensor entities."""

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.vogels_motion_mount_ble.sensor import (
    DistanceSensor,
    RotationSensor,
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
    with patch(  # noqa: SIM117
        "custom_components.vogels_motion_mount_ble.PLATFORMS", [Platform.SENSOR]
    ):
        with patch.object(
            DistanceSensor, "_attr_entity_registry_enabled_default", True
        ):
            with patch.object(
                RotationSensor, "_attr_entity_registry_enabled_default", True
            ):
                await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)
