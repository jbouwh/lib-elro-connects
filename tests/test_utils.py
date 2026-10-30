"""Test the elro connects utilities."""

import pytest

from elro.device import STATE_CLOSED, STATE_NORMAL, STATE_OPEN
from elro.utils import get_device_states


@pytest.mark.parametrize(
    ("device_name", "device_status", "expected_state"),
    [
        ("0101", "0315AAFF", STATE_CLOSED),
        ("0101", "045E66FF", STATE_OPEN),
        ("0013", "0447AAAD", STATE_NORMAL),
    ],
)
def test_get_device_states(device_name, device_status, expected_state):
    """Test the device state is derived using the device type."""
    content = [
        {"device_ID": 1, "device_name": device_name, "device_status": device_status}
    ]
    assert get_device_states(content)[1]["device_state"] == expected_state
