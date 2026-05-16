from __future__ import annotations

from unittest.mock import Mock

import pytest


@pytest.fixture
def hass():
    """Mock HomeAssistant."""
    hass = Mock()
    hass.data = {}
    hass.config_entries._entries = {}
    return hass
