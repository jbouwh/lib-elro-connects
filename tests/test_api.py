"""Test the elro connects API."""

# pylint: disable=line-too-long,redefined-outer-name,protected-access

import asyncio
import json
from threading import local

from unittest.mock import MagicMock, patch
import pytest

from elro.api import K1
from elro.command import (
    GET_SCENES,
    SET_DEVICE_NAME,
    SYN_DEVICE_STATUS,
    GET_DEVICE_NAMES,
    GET_ALL_EQUIPMENT_STATUS,
    TEST_ALARM,
    SILENCE_ALARM,
)

MOCK_AUTH_RESPONSE = b"NAME:ST_1234567890ab\nBIND:0000beef012345678deadbeef0123456\nKEY:deadbeef012345678deadbeef0123456\n"
MOCK_AUTH_RESPONSE_LIMITED = b"NAME:ST_1234567890ab\n"

MOCK_SCENE_RESPONSE = [
    b'{"msgId" : 3640,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 26,"sence_group" : 0,"answer_content" : "000000" }}}\n',
    b'{"msgId" : 3641,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 26,"sence_group" : 1,"answer_content" : "000001" }}}\n',
    b'{"msgId" : 3642,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 26,"sence_group" : 2,"answer_content" : "000002" }}}\n',
    b'{"msgId" : 3643,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 27,"scene_type" : 256 ,"scene_content" : "OVER"}}}\n',
]

MOCK_DEVICE_STATUS_RESPONSE = [
    b'{"msgId" : 3644,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 1,"device_name" : "0013","device_status" : "0364AAFF" }}}\n',
    b'{"msgId" : 3645,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 2,"device_name" : "0013","device_status" : "044B55FF" }}}\n',
    b'{"msgId" : 3646,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 3,"device_name" : "0013","device_status" : "0105FEFF" }}}\n',
    b'{"msgId" : 3647,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 65535,"device_name" : "STATUES","device_status" : "OVER" }}}\n',
]

MOCK_GET_DEVICE_NAME_RESPONSE = [
    b'{"msgId" : 3648,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 17,"answer_content" : "000140404040426567616e6567726f6e6424" }}}\n',
    b'{"msgId" : 3649,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 17,"answer_content" : "000240404045657273746520657461676524" }}}\n',
    b'{"msgId" : 3650,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 17,"answer_content" : "00034040404040404040405a6f6c64657224" }}}\n',
    b'{"msgId" : 3651,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 17,"answer_content" : "NAME_OVER" }}}\n',
]

MOCK_SOCKET_STATUS_ON_RESPONSE = [
    b'{"msgId" : 3652,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 1,"device_name" : "1200","device_status" : "04FF0101" }}}\n',
    b'{"msgId" : 3653,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 65535,"device_name" : "STATUES","device_status" : "OVER" }}}\n',
]
MOCK_SOCKET_STATUS_OFF_RESPONSE = [
    b'{"msgId" : 3654,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 1,"device_name" : "1200","device_status" : "04FF0100" }}}\n',
    b'{"msgId" : 3655,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 19,"device_ID" : 65535,"device_name" : "STATUES","device_status" : "OVER" }}}\n',
]

MOCK_SET_EQUIPMENT_RESPONSE = [
    b'{"msgId" : 8,"action" : "devSend","params" : {"devTid" : "ST_1234567890ab","appTid" :  [],"data" : {"cmdId" : 11,"answer_yes_or_no" : 2 }}}\n'
]


class K1Mock(K1):
    """Mock class."""


@pytest.fixture
def mock_k1_connector():
    """Mock a K1 connector."""

    async def _async_create_datagram_endpoint(protocol_factory, remote_addr):
        """Mock protocol handler"""
        factory = protocol_factory()
        # Mock transport
        transport = MagicMock()
        transport().sendto = MagicMock()
        factory.connection_made(transport)
        # Mock authentication positive response
        factory.datagram_received(MOCK_AUTH_RESPONSE, remote_addr)
        return (transport, factory)

    loop = asyncio.get_event_loop()
    loop.create_datagram_endpoint = MagicMock()
    loop.create_datagram_endpoint.side_effect = _async_create_datagram_endpoint

    return K1Mock("127.0.0.1", "ST_1234567890ab")


@pytest.fixture
def mock_k1_connector_no_key():
    """Mock a K1 connector without api key exposure."""

    async def _async_create_datagram_endpoint(protocol_factory, remote_addr):
        """Mock protocol handler"""
        factory = protocol_factory()
        # Mock transport
        transport = MagicMock()
        transport().sendto = MagicMock()
        factory.connection_made(transport)
        # Mock authentication positive response
        factory.datagram_received(MOCK_AUTH_RESPONSE_LIMITED, remote_addr)
        return (transport, factory)

    loop = asyncio.get_event_loop()
    loop.create_datagram_endpoint = MagicMock()
    loop.create_datagram_endpoint.side_effect = _async_create_datagram_endpoint

    return K1Mock("127.0.0.1", "ST_1234567890ab")


def help_mock_command_reply(mock_k1_connector, response):
    """Mock sendto and send a reply from mock_replies."""
    req = 0

    def sendto(data):  # pylint disable=unused-argument
        """Mock a reply."""
        nonlocal req
        if req >= len(response):
            # No mock responses left
            return
        mock_k1_connector._protocol.datagram_received(
            response[req], mock_k1_connector._remoteaddress
        )
        req += 1
        return

    mock_k1_connector._transport.sendto.side_effect = sendto


@pytest.mark.asyncio
async def test_succesful_initialization_and_disconnect(mock_k1_connector_no_key):
    """Test the connection."""
    await mock_k1_connector_no_key.async_connect()
    assert (
        mock_k1_connector_no_key._transport.sendto.call_args_list[0][0][0]
        == b"IOT_KEY?ST_1234567890ab"
    )
    await mock_k1_connector_no_key.async_disconnect()


@patch("elro.api.TIME_OUT", 0.3)
@pytest.mark.asyncio
async def test_invalid_response(mock_k1_connector):
    """Test timeout on connection."""

    with pytest.raises(K1.K1ConnectionError):
        with patch("tests.test_api.MOCK_AUTH_RESPONSE", b"Invalid_data\n"):
            await mock_k1_connector.async_connect()

    # Start command without valid connection
    with pytest.raises(K1.K1ConnectionError):
        await mock_k1_connector.async_process_command(SYN_DEVICE_STATUS, sence_group=0)


@pytest.mark.asyncio
async def test_missing_key(mock_k1_connector_no_key):
    """Test missing api_key."""

    await mock_k1_connector_no_key.async_connect()

    # Start command without valid connection
    with pytest.raises(K1.K1ConnectionError):
        await mock_k1_connector_no_key.async_process_command(
            SYN_DEVICE_STATUS, sence_group=0
        )


@pytest.mark.asyncio
async def test_get_scenes(mock_k1_connector):
    """Test the getting scenes."""
    await mock_k1_connector.async_connect()

    help_mock_command_reply(mock_k1_connector, MOCK_SCENE_RESPONSE)

    result = await mock_k1_connector.async_process_command(GET_SCENES, sence_group=0)

    assert result[0] == json.loads(MOCK_SCENE_RESPONSE[0])["params"]["data"]


@pytest.mark.asyncio
async def test_sync_device_status(mock_k1_connector):
    """Test get device status."""
    await mock_k1_connector.async_connect()

    help_mock_command_reply(mock_k1_connector, MOCK_DEVICE_STATUS_RESPONSE)

    result = await mock_k1_connector.async_process_command(
        SYN_DEVICE_STATUS, sence_group=0
    )

    assert result[1]["device_type"] == "FIRE_ALARM"
    assert result[1]["signal"] == 3
    assert result[1]["battery"] == 100
    assert result[1]["device_state"] == "NORMAL"

    assert result[2]["device_type"] == "FIRE_ALARM"
    assert result[2]["signal"] == 4
    assert result[2]["battery"] == 75
    assert result[2]["device_state"] == "ALARM"

    assert result[3]["device_type"] == "FIRE_ALARM"
    assert result[3]["signal"] == 1
    assert result[3]["battery"] == 5
    assert result[3]["device_state"] == "UNKNOWN"


@pytest.mark.asyncio
async def test_api_access_properties(mock_k1_connector):
    """Test api access properties."""
    await mock_k1_connector.async_connect()

    assert mock_k1_connector.connector_id == "ST_1234567890ab"
    assert mock_k1_connector.bind_key == "0000beef012345678deadbeef0123456"
    assert mock_k1_connector.api_key == "deadbeef012345678deadbeef0123456"


@pytest.mark.asyncio
async def test_get_device_status(mock_k1_connector):
    """Test sync device status."""
    await mock_k1_connector.async_connect()

    help_mock_command_reply(mock_k1_connector, MOCK_DEVICE_STATUS_RESPONSE)

    result = await mock_k1_connector.async_process_command(GET_ALL_EQUIPMENT_STATUS)

    assert result[1]["device_type"] == "FIRE_ALARM"
    assert result[1]["signal"] == 3
    assert result[1]["battery"] == 100
    assert result[1]["device_state"] == "NORMAL"

    assert result[2]["device_type"] == "FIRE_ALARM"
    assert result[2]["signal"] == 4
    assert result[2]["battery"] == 75
    assert result[2]["device_state"] == "ALARM"

    assert result[3]["device_type"] == "FIRE_ALARM"
    assert result[3]["signal"] == 1
    assert result[3]["battery"] == 5
    assert result[3]["device_state"] == "UNKNOWN"


@pytest.mark.asyncio
async def test_get_device_names(mock_k1_connector):
    """Test sync device status."""
    await mock_k1_connector.async_connect()

    help_mock_command_reply(mock_k1_connector, MOCK_GET_DEVICE_NAME_RESPONSE)

    result = await mock_k1_connector.async_process_command(GET_DEVICE_NAMES)
    assert result[1]["name"] == "Beganegrond"
    assert result[2]["name"] == "Eerste etage"
    assert result[3]["name"] == "Zolder"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id,name,device_name_hex",
    [
        (1, "Barn", "40404040404040404040404261726e24CEE0"),
        (2, "Kitchen", "40404040404040404b69746368656e24126C"),
        (3, "First floor", "40404040466972737420666c6f6f7224581E"),
    ],
)
async def test_set_device_name(mock_k1_connector, id, name, device_name_hex):
    """Test set device name."""
    await mock_k1_connector.async_connect()

    help_mock_command_reply(mock_k1_connector, MOCK_SET_EQUIPMENT_RESPONSE)

    await mock_k1_connector.async_process_command(
        SET_DEVICE_NAME, device_ID=id, device_name=name
    )

    assert json.loads(
        mock_k1_connector._transport.sendto.call_args_list[1][0][0].decode("utf-8")
    ) == json.loads(
        '{"msgId": 1, "action": "appSend", "params": {"devTid": "ST_1234567890ab", "ctrlKey": "deadbeef012345678deadbeef0123456", "appTid": 1, "data": {"cmdId": 5, "device_ID": '
        + str(id)
        + ', "device_name": "'
        + device_name_hex
        + '"}}}'
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id,mode,response",
    [
        (
            1,
            TEST_ALARM,
            "17000000",
        ),
        (
            1,
            SILENCE_ALARM,
            "00000000",
        ),
        (
            2,
            TEST_ALARM,
            "17000000",
        ),
        (
            2,
            SILENCE_ALARM,
            "00000000",
        ),
    ],
)
async def test_set_test_alarm(mock_k1_connector, id, mode, response):
    """Test set device name."""
    await mock_k1_connector.async_connect()

    help_mock_command_reply(mock_k1_connector, MOCK_SET_EQUIPMENT_RESPONSE)

    await mock_k1_connector.async_process_command(mode, device_ID=id)

    received = json.loads(
        mock_k1_connector._transport.sendto.call_args_list[1][0][0].decode("utf-8")
    )
    assert received["params"]["data"]["device_ID"] == id
    assert received["params"]["data"]["device_status"] == response


@pytest.mark.asyncio
async def test_configure(mock_k1_connector):
    """Test configuring the connector settings."""
    await mock_k1_connector.async_connect()
    assert mock_k1_connector._remoteaddress == ("127.0.0.1", 1025)
    await mock_k1_connector.async_configure("127.0.0.2", 1024)
    assert mock_k1_connector._remoteaddress == ("127.0.0.2", 1024)


@pytest.mark.asyncio
async def test_key_override():
    """Test overriding the API key."""

    # auth response WITH key to override
    auth_response = MOCK_AUTH_RESPONSE

    async def _async_create_datagram_endpoint(protocol_factory, remote_addr):
        """Mock protocol handler"""
        factory = protocol_factory()
        # Mock transport
        transport = MagicMock()
        transport().sendto = MagicMock()
        factory.connection_made(transport)
        # Mock authentication positive response
        factory.datagram_received(auth_response, remote_addr)
        return (transport, factory)

    loop = asyncio.get_event_loop()
    loop.create_datagram_endpoint = MagicMock()
    loop.create_datagram_endpoint.side_effect = _async_create_datagram_endpoint

    # test override provided key

    mock_k1_connector = K1Mock("127.0.0.1", "ST_1234567890ab", api_key="override_key")
    await mock_k1_connector.async_connect()

    assert mock_k1_connector.connector_id == "ST_1234567890ab"
    assert mock_k1_connector.bind_key == "0000beef012345678deadbeef0123456"
    assert mock_k1_connector.api_key == "override_key"

    # test add missing key with auth response WITHOUT key
    auth_response = MOCK_AUTH_RESPONSE_LIMITED

    mock_k1_connector = K1Mock("127.0.0.1", "ST_1234567890ab", api_key="override_key")
    await mock_k1_connector.async_connect()

    assert mock_k1_connector.connector_id == "ST_1234567890ab"
    assert mock_k1_connector.bind_key is None
    assert mock_k1_connector.api_key == "override_key"
