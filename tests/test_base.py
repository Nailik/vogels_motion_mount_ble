import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.vogels_motion_mount_ble.base import (
    VogelsMotionMountBleBaseEntity,
)


@pytest.mark.asyncio
async def test_handle_coordinator_update_triggers_state_write(mock_coord: MagicMock):
    """Test that _handle_coordinator_update calls async_write_ha_state."""

    # Create entity with coordinator
    entity = VogelsMotionMountBleBaseEntity(mock_coord)

    # Patch async_write_ha_state
    entity.async_write_ha_state = AsyncMock()

    # Call method under test
    entity._handle_coordinator_update()

    # Verify async_write_ha_state was called
    entity.async_write_ha_state.assert_called_once()
