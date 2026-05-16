from __future__ import annotations

import os

COMMAND_FILES = ["switch.py", "button.py", "lock.py", "services.yaml"]


def test_no_command_files_in_integration():
    integration_dir = os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "cesar_smart"
    )
    for fname in COMMAND_FILES:
        path = os.path.join(integration_dir, fname)
        assert not os.path.exists(path), f"Command file {fname} must not exist"


def test_no_send_command_in_api():
    from custom_components.cesar_smart.api import CesarSmartApiClient
    assert not hasattr(CesarSmartApiClient, "send_command")
    assert not hasattr(CesarSmartApiClient, "async_send_command")


def test_no_post_commands_in_api():
    with open(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "cesar_smart",
            "api.py",
        ),
        encoding="utf-8",
    ) as f:
        content = f.read()
    assert "commands" not in content, "api.py must not reference 'commands'"


def test_no_switch_button_lock_platforms():
    from custom_components.cesar_smart.const import PLATFORMS
    from homeassistant.const import Platform
    assert Platform.SWITCH not in PLATFORMS
    assert Platform.BUTTON not in PLATFORMS
    assert Platform.LOCK not in PLATFORMS
