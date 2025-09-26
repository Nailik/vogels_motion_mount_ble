from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from typing import Any, Dict

DOMAIN = "vogels_motion_mount_ble"
MOCKED_CONF_ENTRY_ID = "some-entry-id"
MOCKED_CONF_ENTRY_UNIQUE_ID = "some-unique-id"
MOCKED_CONF_MAC = "AA:BB:CC:DD:EE:FF"
MOCKED_CONF_NAME = "Mount"
MOCKED_CONF_PIN = 1234
CONF_MAC = "conf_mac"
CONF_NAME = "conf_name"
CONF_PIN = "conf_pin"
CONF_ERROR = "base"
MIN_HA_VERSION = "2025.6.0"

MOCKED_CONFIG: Dict[str, Any] = {
    CONF_MAC: MOCKED_CONF_MAC,
    CONF_NAME: MOCKED_CONF_NAME,
    CONF_PIN: MOCKED_CONF_PIN,
}


async def setup_integration(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Fixture for setting up the component."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
