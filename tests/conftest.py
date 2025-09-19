"""Fixtures for testing."""

import pytest
import sys
import types


def pytest_configure():
    # Fake `resource` for Windows
    if sys.platform == "win32" and "resource" not in sys.modules:
        sys.modules["resource"] = types.ModuleType("resource")

    # Fake `aiousbwatcher` for Linux/WSL test env
    if "aiousbwatcher" not in sys.modules:
        fake = types.ModuleType("aiousbwatcher")

        class AIOUSBWatcher:
            def __init__(self, *args, **kwargs):
                self._callbacks = []

            def async_start(self):
                return

            def async_stop(self):
                return

            def async_register_callback(self, callback):
                self._callbacks.append(callback)

            def async_unregister_callback(self, callback):
                if callback in self._callbacks:
                    self._callbacks.remove(callback)

        class InotifyNotAvailableError(Exception):
            pass

        fake.AIOUSBWatcher = AIOUSBWatcher  # pyright: ignore[reportAttributeAccessIssue]
        fake.InotifyNotAvailableError = InotifyNotAvailableError  # pyright: ignore[reportAttributeAccessIssue]
        sys.modules["aiousbwatcher"] = fake


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return
