"""Elro device class models."""

from enum import Enum


class DeviceType(Enum):
    """
    The DeviceType defines which kind of Elro device this is
    """

    CO_ALARM = "0000", "1000", "2000", "0008", "1008", "2008", "000E", "100E", "200E"
    GAS_ALARM = "0002", "1002", "2002", "1006", "000A", "100A", "200A"
    SMOKE_ALARM = "0001", "1001", "2001", "0009", "1009", "2009"
    WATER_ALARM = "0004", "1004", "2004", "000C", "100C", "200C", "0012", "1012", "2012"
    HEAT_ALARM = "0003", "1003", "2003", "000B", "100B", "200B", "0011", "1011", "2011"
    FIRE_ALARM = "0005", "1109", "2109", "000D", "100D", "200D", "0013", "1013", "2013"

    GUARD = "0210", "1210", "2210"  # access control
    TEMPERATURE_SENSOR = "0102", "1102", "2102"  # TH_CHECK
    DOOR_WINDOW_SENSOR = "0101", "1101", "2101"  # DOOR_CHECK

    LOCK = "1213"
    MODE_BUTTON = "0305"
    BUTTON = "0301", "1301", "2301"
    LAMP = "020A", "120A", "220A"
    SOCKET = "0200", "1200", "2200"
    TWO_SOCKET = "0201", "1201", "2201"
    VALVE = "0208", "1208", "2208"
    CURTAIN = "0209", "1209", "2209"
    TEMP_CONTROL = "0215", "1215", "2215"
    DIMMING_MODULE = "0214", "1214", "2214"

    SOS_KEY = "0300", "1300", "2300"
    PIR_CHECK = "0100", "1100", "2100"

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj  # pylint: disable=maybe-no-member
        obj._all_values = values
        return obj

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}.{self._name_}: "  # pylint: disable=maybe-no-member
            f"{', '.join([repr(v) for v in self._all_values])}>"
        )


# Represent alarm device types
ALARM_CO = "CO_ALARM"
ALARM_FIRE = "FIRE_ALARM"
ALARM_HEAT = "HEAT_ALARM"
ALARM_SMOKE = "SMOKE_ALARM"
ALARM_WATER = "WATER_ALARM"

# Represent device state attributes
ATTR_BATTERY_LEVEL = "battery"
ATTR_DEVICE_TYPE = "device_type"
ATTR_DEVICE_STATE = "device_state"
ATTR_SIGNAL = "signal"

# Represent the state of a device.
DEVICE_STATE = {
    "12": "FAULT",
    "15": "SILENCE",
    "17": "TEST ALARM",
    "19": "FIRE ALARM",
    "22": "FIRE ALARM",
    "1B": "SILENCE",
    "BB": "TEST ALARM",
    "55": "ALARM",  # OPEN window sensor
    "AA": "NORMAL",  # CLOSED window sensor
    "FE": "UNKNOWN",
    "FF": "OFFLINE",
}

STATE_ALARM = "ALARM"
STATE_FAULT = "FAULT"
STATE_FIRE_ALARM = "FIRE ALARM"
STATE_NORMAL = "NORMAL"
STATE_OFFLINE = "OFFLINE"
STATE_SILENCE = "SILENCE"
STATE_TEST_ALARM = "TEST ALARM"
STATE_UNKNOWN = "UNKNOWN"

STATES_ON = (STATE_ALARM, STATE_FIRE_ALARM, STATE_TEST_ALARM)
STATES_OFFLINE = (STATE_OFFLINE,)
