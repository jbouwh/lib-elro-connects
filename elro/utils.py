"""Utilities to support Elro Connects P1 API."""

from __future__ import annotations

import json
import logging
import collections
from typing import Any

from elro.device import DeviceType, DEVICE_STATE


# From the ByteUtil class, needed by CRC_maker
AUCHCRCHI = (
    b"\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00\xc1"
    b"\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01"
    b"\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A"
    b"\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0"
    b"\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01"
    b"\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@"
    b"\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1"
    b"\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00"
    b"\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A"
    b"\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0"
    b"\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01"
    b"\xc0\x80A\x00\xc1\x81@"
)
# From the ByteUtil class, needed by CRC_maker
AUCHCRCLO = (
    b"\x00\xc0\xc1\x01\xc3\x03\x02\xc2\xc6\x06\x07\xc7\x05\xc5\xc4\x04\xcc\x0c\r"
    b"\xcd\x0f\xcf\xce\x0e\n\xca\xcb\x0b\xc9\t\x08\xc8\xd8\x18\x19\xd9\x1b\xdb\xda"
    b"\x1a\x1e\xde\xdf\x1f\xdd\x1d\x1c\xdc\x14\xd4\xd5\x15\xd7\x17\x16\xd6\xd2\x12"
    b"\x13\xd3\x11\xd1\xd0\x10\xf001\xf13\xf3\xf226\xf6\xf77\xf554\xf4<\xfc\xfd="
    b"\xff?>\xfe\xfa:;\xfb9\xf9\xf88(\xe8\xe9)\xeb+*\xea\xee./\xef-\xed\xec,\xe4$%"
    b"\xe5'\xe7\xe6&\"\xe2\xe3#\xe1! \xe0\xa0`a\xa1c\xa3\xa2bf\xa6\xa7g\xa5ed\xa4l"
    b"\xac\xadm\xafon\xae\xaajk\xabi\xa9\xa8hx\xb8\xb9y\xbb{z\xba\xbe~\x7f\xbf}\xbd"
    b"\xbc|\xb4tu\xb5w\xb7\xb6vr\xb2\xb3s\xb1qp\xb0P\x90\x91Q\x93SR\x92\x96VW\x97U"
    b"\x95\x94T\x9c\\]\x9d_\x9f\x9e^Z\x9a\x9b[\x99YX\x98\x88HI\x89K\x8b\x8aJN\x8e"
    b"\x8fO\x8dML\x8cD\x84\x85E\x87GF\x86\x82BC\x83A\x81\x80@"
)


def get_string_from_ascii(input_string):
    """
    This function is reversed engineered and translated to python
    based on the CoderUtils class in the ELRO Android app

    :param input: A hex string
    :return: A string
    """
    try:
        if len(input_string) != 32:
            raise ValueError("input {} has not the required length of 32.")

        byt = bytearray.fromhex(input_string)
        name = "".join(map(chr, byt))
        name = name.replace("@", "").replace("$", "")
    except ValueError as error:
        raise error

    return name


def get_ascii(input_string: str) -> str | None:
    """Encode a string to hex for API use."""
    #
    # This function is partially reversed engineered and translated to python
    # based on the CoderUtils class in the ELRO Android app

    # :param input: A string
    # :return: A hex string

    # Pattern("^[_\-a-zA-Z0-9 ]*$"

    countf = 0

    countf = 15 - len(input_string.encode("GBK"))

    if countf < 0:
        logging.error("Input is to long '%s'", input_string)
        return None

    str_whitespace = ""
    for _ in range(countf):
        str_whitespace += "@"

    new_name = str_whitespace + input_string + "$"

    # This is the original code and thus where the python code differs.
    # Because this is not used, GBK encoding is probably not fully supported

    # byte[] nameBt = new byte[16];
    # try {
    #    nameBt = newname.getBytes("GBK");
    # } catch (UnsupportedEncodingException e) {
    #    e.printStackTrace();
    # }

    # String ds = "";
    # for(int i=0;i<nameBt.length;i++){
    #    String str = ByteUtil.convertByte2HexString(nameBt[i]);
    #    ds+=str;
    # }

    # These two functions are also used, from the ByteUtils
    # public static String convertByte2HexString(byte b) {
    #    char u8 = convertByte2Uint8(b);
    #    String buf = Integer.toHexString(u8);
    #    if (buf.length() == 1) {
    #        buf = '0' + buf;
    #    }
    #    return buf;
    # }

    # public static char combine2bytesToU16(byte high, byte low) {
    #    char highU8 = convertByte2Uint8(high);
    #    char lowU8 = convertByte2Uint8(low);
    #    return (char) (highU8 << 8 | lowU8);
    # }

    return new_name.encode("GBK").hex()


def crc_maker(msg):
    """
    This function is reversed engineered and translated to python
    based on the ByteUtil class in the ELRO Android app

    :param input: The string to create a CRC for
    :return: A CRC string
    """
    crc_hi_1 = 0
    crc_lo_1 = 0
    msg_length = len(msg)
    index = 0
    crc_index = 0
    uch_crc_hi = 0xFF
    uch_crc_lo = 0xFF

    while index < msg_length:
        char_code = ord(msg[index])

        crc_index = uch_crc_hi ^ char_code
        uch_crc_hi = uch_crc_lo ^ AUCHCRCHI[crc_index]
        uch_crc_lo = AUCHCRCLO[crc_index]

        index = index + 1

    crc_lo_1 = uch_crc_hi
    crc_lo_2 = int(crc_lo_1)
    crc_lo_3 = hex(crc_lo_2)[2:]
    if len(crc_lo_3) < 2:
        crc_lo_3 = "0" + crc_lo_3

    crc_hi_1 = uch_crc_lo
    crc_hi_2 = int(crc_hi_1)
    crc_hi_3 = hex(crc_hi_2)[2:]
    if len(crc_hi_3) < 2:
        crc_hi_3 = "0" + crc_hi_3

    return f"{crc_hi_3.upper()}{crc_lo_3.upper()}"


def crc_maker_char(msg):
    """
    This function is reversed engineered and translated to python
    based on the ByteUtil class in the ELRO Android app

    :param input: The string to create a CRC for
    :return: A CRC string
    """

    crc_hi_1 = 0
    crc_lo_1 = 0
    index = 0
    crc_index = 0
    uch_crc_hi = 0xFF
    uch_crc_lo = 0xFF

    msg_length = int(len(msg) / 2)
    content = []

    for _ in range(msg_length):
        val = chr(int((msg[0:2]), 16))
        content.append(val)
        msg = msg[2:]

    while index < msg_length:
        char_code = ord(content[index])

        crc_index = uch_crc_hi ^ char_code
        uch_crc_hi = uch_crc_lo ^ AUCHCRCHI[crc_index]
        uch_crc_lo = AUCHCRCLO[crc_index]

        index = index + 1

    crc_lo_1 = uch_crc_hi
    crc_lo_2 = int(crc_lo_1)
    crc_lo_3 = hex(crc_lo_2)[2:]
    if len(crc_lo_3) < 2:
        crc_lo_3 = "0" + crc_lo_3

    crc_hi_1 = uch_crc_lo
    crc_hi_2 = int(crc_hi_1)
    crc_hi_3 = hex(crc_hi_2)[2:]
    if len(crc_hi_3) < 2:
        crc_hi_3 = "0" + crc_hi_3

    return f"{crc_hi_3.upper()}{crc_lo_3.upper()}"


def get_eq_crc(devices):
    """
    Builds a CRC string based on device id and device status. This function is reverse engineered
    and translated to python. It is based on the CoderUtils class in the elro app :param devices:.
    A dictionary of devices statuses, where the id of the device is the index of the dict
    """
    sorted_devices = collections.OrderedDict(sorted(devices.items()))
    list_length = int(list(sorted_devices.keys())[-1])

    status_crc = ""
    for i in range(list_length + 1):
        if i + 1 in sorted_devices:
            status_crc += crc_maker_char(sorted_devices[i + 1])
        elif i < (list_length):
            status_crc += "0000"

    num = ""
    list_length_for_hex = hex((list_length * 2 + 2))[2:]
    if len(list_length_for_hex) < 4:
        i = 4 - len(list_length_for_hex)
        num = list_length_for_hex.rjust(i + len(list_length_for_hex), "0")
    else:
        num = list_length_for_hex

    return num + status_crc


def update_state_data(
    data: dict[int, dict[str, Any]] | None,
    data_update: dict[int, dict[str, Any]] | None,
) -> None:
    "Update the state."
    if data_update is None or data is None:
        return
    for key in data_update.keys():
        if not key in data:
            data[key] = data_update[key]
        else:
            data[key].update(data_update[key])


def get_device_names(content: list) -> dict:
    """Return device names."""
    # answer_content
    return {
        int(data["answer_content"][0:4], 16): {
            "name": get_string_from_ascii(data["answer_content"][4:])
        }
        for data in content
    }


def set_device_name(argv: dict) -> None:
    """Convert the device_name attribute to a hex representation including crc."""
    if device_name := argv.get("device_name"):
        device_name_hex = get_ascii(device_name)
        crc = crc_maker(device_name)
        argv["device_name"] = f"{device_name_hex}{crc}"
    else:
        raise ValueError("Value for device_name is not set!")


def get_device_states(content: list) -> dict:
    """Return device states."""
    return_dict = {}
    for hexdata in content:
        try:
            device_type = DeviceType(hexdata["device_name"]).name
        except ValueError:
            # Unsupported record, skip and continue silently
            continue
        device_state = hexdata["device_status"][4:6]
        return_dict[hexdata["device_ID"]] = {
            "device_type": device_type,
            "signal": int(hexdata["device_status"][0:2], 16),
            "battery": int(hexdata["device_status"][2:4], 16),
            "device_state": DEVICE_STATE.get(
                device_state, device_state
            ),  # return hex device state if it is not known
            "device_status_data": hexdata,
        }
    return return_dict


def get_default(content: list) -> dict:
    """Return content from ascii."""
    index = 0
    return_dict = {}
    for line in content:
        return_dict[index] = line
        index += 1

    return return_dict


def validate_json(raw_data: bytes) -> dict:
    """Process the JSON basis response, work-a-round synatx errors."""
    json_string = raw_data.decode("utf-8")
    try:
        data = json.loads(json_string)
    except json.decoder.JSONDecodeError:
        # Try correct the malformed JSON status string missing to closing brackets
        data = json.loads(json_string + "}}")
    return data
