"""Tests for base entities."""

from unittest.mock import AsyncMock

import pytest

from custom_components.vogels_motion_mount_ble.base import (
    VogelsMotionMountBleBaseEntity,
)
from custom_components.vogels_motion_mount_ble.coordinator import (
    VogelsMotionMountBleCoordinator,
)


@pytest.mark.asyncio
async def test_handle_coordinator_update_triggers_state_write(
    mock_coord: VogelsMotionMountBleCoordinator,
):
    """Test that _handle_coordinator_update calls async_write_ha_state."""

    # Create entity with coordinator
    entity = VogelsMotionMountBleBaseEntity(mock_coord)

    # Patch async_write_ha_state
    entity.async_write_ha_state = AsyncMock()

    # Call method under test
    entity._handle_coordinator_update()  # noqa: SLF001

    # Verify async_write_ha_state was called
    entity.async_write_ha_state.assert_called_once()
