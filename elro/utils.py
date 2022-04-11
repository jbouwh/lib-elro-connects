import logging
import collections

from valideer import accepts, Pattern


# From the ByteUtil class, needed by CRC_maker
AUCHCRCHI = b"\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@\x00\xc1\x81@\x01\xc0\x80A\x00\xc1\x81@\x01\xc0\x80A\x01\xc0\x80A\x00\xc1\x81@"
# From the ByteUtil class, needed by CRC_maker
AUCHCRCLO = b"\x00\xc0\xc1\x01\xc3\x03\x02\xc2\xc6\x06\x07\xc7\x05\xc5\xc4\x04\xcc\x0c\r\xcd\x0f\xcf\xce\x0e\n\xca\xcb\x0b\xc9\t\x08\xc8\xd8\x18\x19\xd9\x1b\xdb\xda\x1a\x1e\xde\xdf\x1f\xdd\x1d\x1c\xdc\x14\xd4\xd5\x15\xd7\x17\x16\xd6\xd2\x12\x13\xd3\x11\xd1\xd0\x10\xf001\xf13\xf3\xf226\xf6\xf77\xf554\xf4<\xfc\xfd=\xff?>\xfe\xfa:;\xfb9\xf9\xf88(\xe8\xe9)\xeb+*\xea\xee./\xef-\xed\xec,\xe4$%\xe5'\xe7\xe6&\"\xe2\xe3#\xe1! \xe0\xa0`a\xa1c\xa3\xa2bf\xa6\xa7g\xa5ed\xa4l\xac\xadm\xafon\xae\xaajk\xabi\xa9\xa8hx\xb8\xb9y\xbb{z\xba\xbe~\x7f\xbf}\xbd\xbc|\xb4tu\xb5w\xb7\xb6vr\xb2\xb3s\xb1qp\xb0P\x90\x91Q\x93SR\x92\x96VW\x97U\x95\x94T\x9c\\]\x9d_\x9f\x9e^Z\x9a\x9b[\x99YX\x98\x88HI\x89K\x8b\x8aJN\x8e\x8fO\x8dML\x8cD\x84\x85E\x87GF\x86\x82BC\x83A\x81\x80@"


def get_string_from_ascii(input_string):
    """
    This function is reversed engineered and translated to python
    based on the CoderUtils class in the ELRO Android app

    :param input: A hex string
    :return: A string
    """
    try:
        if len(input_string) != 32:
            return ""

        byt = bytearray.fromhex(input_string)
        name = "".join(map(chr, byt))
        name = name.replace("@", "").replace("$", "")
    except:
        return ""

    return name


@accepts(
    input_string=Pattern("^[_\-a-zA-Z0-9 ]*$")
)  # Not fully supporting a wide range of characters due to partial implementation
def get_ascii(input_string):
    """
    This function is partially reversed engineered and translated to python
    based on the CoderUtils class in the ELRO Android app

    :param input: A string
    :return: A hex string
    """
    countf = 0

    try:
        countf = 15 - len(input_string.encode("GBK"))
    except Exception as exception:
        logging.error(f"Unable to convert '{input_string}' with error: {exception}")
        return

    if countf < 0:
        logging.error(f"Input is to long '{input_string}'")
        return

    str_whitespace = ""
    for i in range(countf):
        str_whitespace += "@"

    new_name = str_whitespace + input_string + "$"

    # This is the original code and thus where the python code differs. Because this is not used, GBK encoding is probably not fully supported

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
    CRCHi = 0
    CRCLo = 0
    msgLength = len(msg)
    index = 0
    CRCIndex = 0
    uchCRCHi = 0xFF
    uchCRCLo = 0xFF

    while index < msgLength:
        charCode = ord(msg[index])

        CRCIndex = uchCRCHi ^ charCode
        uchCRCHi = uchCRCLo ^ AUCHCRCHI[CRCIndex]
        uchCRCLo = AUCHCRCLO[CRCIndex]

        index = index + 1

    CRCLo = uchCRCHi
    crcLo = int(CRCLo)
    crcLo1 = hex(crcLo)[2:]
    if len(crcLo1) < 2:
        crcLo1 = "0" + crcLo1

    CRCHi = uchCRCLo
    crcHi = int(CRCHi)
    crcHi1 = hex(crcHi)[2:]
    if len(crcHi1) < 2:
        crcHi1 = "0" + crcHi1

    return f"{crcHi1.upper()}{crcLo1.upper()}"


def crc_maker_char(msg):
    """
    This function is reversed engineered and translated to python
    based on the ByteUtil class in the ELRO Android app

    :param input: The string to create a CRC for
    :return: A CRC string
    """

    CRCHi = 0
    CRCLo = 0
    msgLength = int(len(msg) / 2)
    content = []
    for i in range(msgLength):
        val = chr(int((msg[0:2]), 16))
        content.append(val)
        msg = msg[2:]

    index = 0
    CRCIndex = 0
    uchCRCHi = 0xFF
    uchCRCLo = 0xFF

    while index < msgLength:
        charCode = ord(content[index])

        CRCIndex = uchCRCHi ^ charCode
        uchCRCHi = uchCRCLo ^ AUCHCRCHI[CRCIndex]
        uchCRCLo = AUCHCRCLO[CRCIndex]

        index = index + 1

    CRCLo = uchCRCHi
    crcLo = int(CRCLo)
    crcLo1 = hex(crcLo)[2:]
    if len(crcLo1) < 2:
        crcLo1 = "0" + crcLo1

    CRCHi = uchCRCLo
    crcHi = int(CRCHi)
    crcHi1 = hex(crcHi)[2:]
    if len(crcHi1) < 2:
        crcHi1 = "0" + crcHi1

    return f"{crcHi1.upper()}{crcLo1.upper()}"


def get_eq_crc(devices):
    """
    Builds a CRC string based on device id and device status. This function is reverse engineered
    and translated to python. It is based on the CoderUtils class in the elro app
    :param devices: An dictionary of devices statuses, where the id of the device is the index of the dict
    """
    sorted_devices = collections.OrderedDict(sorted(devices.items()))
    list_length = int(list(sorted_devices.keys())[-1])

    status_crc = ""
    for i in range(list_length + 1):
        if (i + 1) in sorted_devices:
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
