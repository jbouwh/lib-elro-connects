"""Test the elro connects temperature sensor."""

import pytest

from elro.device import (
    ATTR_DEVICE_STATE,
    ATTR_HUMIDITY,
    ATTR_TEMPERATURE,
    STATE_NORMAL,
    STATE_OFFLINE,
)
from elro.utils import get_device_states


@pytest.mark.parametrize("device_name", ["0102", "1102", "2102"])
@pytest.mark.parametrize(
    ("device_status", "temperature", "humidity"),
    [
        ("04501537", 21, 55),
        ("0450FB40", -5, 64),
        ("04500000", 0, 0),
        ("0450D832", -40, 50),
    ],
)
def test_temperature_sensor(device_name, device_status, temperature, humidity):
    """Test the temperature and humidity of a temperature sensor."""
    content = [
        {"device_ID": 1, "device_name": device_name, "device_status": device_status}
    ]
    state = get_device_states(content)[1]
    assert state[ATTR_DEVICE_STATE] == STATE_NORMAL
    assert state[ATTR_TEMPERATURE] == temperature
    assert state[ATTR_HUMIDITY] == humidity


@pytest.mark.parametrize(
    "device_status",
    [
        "04506564",  # 101 degrees Celsius
        "0450D732",  # -41 degrees Celsius
        "04501565",  # 101 % humidity
        "FFFFFFFF",  # 255 % humidity
    ],
)
def test_temperature_sensor_invalid(device_status):
    """Test a temperature sensor with out of range values is offline."""
    content = [{"device_ID": 1, "device_name": "0102", "device_status": device_status}]
    state = get_device_states(content)[1]
    assert state[ATTR_DEVICE_STATE] == STATE_OFFLINE
    assert ATTR_TEMPERATURE not in state
    assert ATTR_HUMIDITY not in state


def test_other_device_types_have_no_temperature():
    """Test other device types do not get a temperature or humidity."""
    content = [{"device_ID": 1, "device_name": "0013", "device_status": "04501537"}]
    state = get_device_states(content)[1]
    assert ATTR_TEMPERATURE not in state
    assert ATTR_HUMIDITY not in state
