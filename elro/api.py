"""Elro connects API."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import TypedDict
from elro.command import (
    Command,
    CommandAttributes,
    ACK_APP,
    CMD_CONNECT,
)
from elro.utils import (
    get_default,
    get_device_names,
    get_device_states,
    update_state_data,
    validate_json,
)

ATTR_BIND = "BIND"
ATTR_KEY = "KEY"
ATTR_NAME = "NAME"

APP_ID = 0

TIMEOUT = 10
INTERVAL = 5
UDP_PORT_NO = 1025

_LOGGER = logging.getLogger(__name__)

# GET_DEVICE_NAMES returns a dict[{device_id}, {device_name}]
GET_DEVICE_NAMES = CommandAttributes(
    cmd_id=Command.GET_DEVICE_NAME,
    additional_attributes={"device_ID": 0},
    receive_types=[Command.DEVICE_NAME_REPLY],
    content_field="answer_content",
    content_sync_finished="NAME_OVER",
    content_transformer=get_device_names,
)

# SYN DEVICE_STATUS
SYN_DEVICE_STATUS = CommandAttributes(
    cmd_id=Command.SYN_DEVICE_STATUS,
    additional_attributes={"device_status": ""},
    receive_types=[Command.DEVICE_STATUS_UPDATE, Command.DEVICE_ALARM_TRIGGER],
    content_field="device_status",
    content_sync_finished="OVER",
    content_transformer=get_device_states,
)

# GET_ALL_EQUIPMENT_STATUS
GET_ALL_EQUIPMENT_STATUS = CommandAttributes(
    cmd_id=Command.GET_ALL_EQUIPMENT_STATUS,
    additional_attributes={"device_status": ""},
    receive_types=[Command.DEVICE_STATUS_UPDATE, Command.DEVICE_ALARM_TRIGGER],
    content_field="device_status",
    content_sync_finished="OVER",
    content_transformer=get_device_states,
)

# TEST_ALARM
TEST_ALARM = CommandAttributes(
    cmd_id=Command.EQUIPMENT_CONTROL,
    additional_attributes={"device_ID": 0, "device_status": "17000000"},
    receive_types=[Command.ANSWER_YES_OR_NO],
    content_field="answer_yes_or_no",
    content_sync_finished=2,
    content_transformer=None,
)

SILENCE_ALARM = CommandAttributes(
    cmd_id=Command.EQUIPMENT_CONTROL,
    additional_attributes={"device_ID": 0, "device_status": "00000000"},
    receive_types=[Command.ANSWER_YES_OR_NO],
    content_field="answer_yes_or_no",
    content_sync_finished=2,
    content_transformer=None,
)

# GET_SCENES returns a dict[{scene_id}, None]
# NOTE: If queried frequently not all data is provisioned all the time
GET_SCENES = CommandAttributes(
    cmd_id=Command.SYN_SCENE,
    additional_attributes={
        "sence_group": 0,
        "answer_content": "",
        "scene_content": "",
    },
    receive_types=[
        Command.SENCE_GROUP_DETAIL,
        Command.SCENE_TYPE,
        Command.SENCE_GROUP,
    ],
    content_field="scene_content",
    content_sync_finished="OVER",
    content_transformer=get_default,
)


class K1UDPHandler:
    """UDP test class."""

    def __init__(self, message, on_con_lost, datagram_data):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None
        self.datagram_data = datagram_data
        self.last_exc = None

    def connection_made(self, transport):
        """Connection made."""
        self.transport = transport
        self.transport.sendto(self.message)

    def datagram_received(self, data, addr):
        """Datagram reveived."""
        if not self.datagram_data.done():
            self.datagram_data.set_result((data, addr))

    def close_connection(self):
        """Close the connection."""
        self.transport.close()

    def error_received(self, exc):
        """Error received."""
        print("Error received:", exc)
        self.last_exc = exc

    def connection_lost(self, exc):
        """Connection lost."""
        self.last_exc = exc
        self.on_con_lost.set_result(True)
        if not self.datagram_data.done():
            self.datagram_data.set_result((None, None))


class K1:
    """API class to Elro connects K1 adapter."""

    class K1ConnectionError(Exception):
        """K1 exception class."""

        def __init__(self, message: str = "K1 connection error"):
            self.message = message
            super().__init__(self.message)

    class Reponse(TypedDict):
        """API Response class"""

        received: int

    def __init__(self, ipaddress: str, k1_id: str, port: int = 1025) -> None:
        """Initialize the module."""
        self.transport = None
        self.protocol = None
        self.ipaddress = ipaddress
        self.k1_id = k1_id
        self.port = port
        self.bind = self.key = None
        self.session = {}
        self.msg_id = 0
        self.loop = None
        self.lock = asyncio.Lock()

    async def async_connect(self) -> str:
        """Connect to the K1 hub."""
        self.loop = asyncio.get_running_loop()
        on_conn_lost, datagram_data = (
            self.loop.create_future(),
            self.loop.create_future(),
        )
        payload = (CMD_CONNECT + self.k1_id).encode("utf-8")
        await self.lock.acquire()
        try:
            self.transport, self.protocol = await self.loop.create_datagram_endpoint(
                lambda: K1UDPHandler(payload, on_conn_lost, datagram_data),
                remote_addr=(self.ipaddress, self.port),
            )
            await asyncio.wait_for(datagram_data, 15.0)
            if data := datagram_data.result():
                return data[0].decode("utf-8")
            raise K1.K1ConnectionError(
                "Not received the expected result, cannot connect to "
                f"hub {self.ipaddress} with id {self.k1_id}."
            )
        except TimeoutError:
            pass
        finally:
            self.lock.release()
        return None

    async def async_disconnect(self) -> str:
        """Disconnect from the K1 hub."""
        await self.lock.acquire()
        try:
            if not self.protocol.on_con_lost.done():
                self.transport.close()
        finally:
            self.lock.release()

    def _prepare_command(self, command_data: dict) -> bytes:
        """
        Construct a valid message from data
        :param data: A string containing data to be send to the K1
        :return: A json message
        """
        self.msg_id += 1

        command = {
            "msgId": self.msg_id,
            "action": "appSend",
            "params": {
                "devTid": self.session[ATTR_NAME],
                "ctrlKey": self.session[ATTR_KEY],
                "appTid": 1,
                "data": command_data,
            },
        }
        return json.dumps(command).encode("utf-8")

    async def async_process_command(
        self, attributes: CommandAttributes, **argv: dict | None
    ) -> dict | None:
        """Get device names."""

        iteration = 0
        command_data = {
            "cmdId": attributes["cmd_id"].value,
        }
        command_data.update(attributes["additional_attributes"])
        if argv:
            command_data.update(argv)
        command = self._prepare_command(command_data)
        contentlist = []
        await self.lock.acquire()
        try:
            self.protocol.datagram_data = self.loop.create_future()
            self.transport.sendto(command)
            while True:
                # Run loop until last item
                try:
                    await asyncio.wait_for(self.protocol.datagram_data, TIMEOUT)
                except asyncio.TimeoutError:
                    print("TIMEOUT")
                    break
                if raw_data := self.protocol.datagram_data.result():
                    iteration += 1
                    _LOGGER.debug(
                        "command attributes: %s received[%s]: %s",
                        command_data,
                        iteration,
                        raw_data[0].decode("utf-8").strip()
                        if raw_data[0] is not None
                        else None,
                    )
                    self.protocol.datagram_data = self.loop.create_future()
                    data = validate_json(raw_data[0])
                    params = data["params"]
                    cmd_id = params["data"]["cmdId"]
                    content = params["data"].get(attributes["content_field"], "")
                    if Command(cmd_id) in attributes["receive_types"]:
                        self.transport.sendto(ACK_APP.encode("utf-8"))
                        if content == attributes["content_sync_finished"]:
                            break
                        if content:
                            contentlist.append(params["data"])

                else:
                    self.transport.sendto(ACK_APP.encode("utf-8"))
                    break
        finally:
            self.lock.release()
        return (
            attributes["content_transformer"](contentlist)
            if attributes.get("content_transformer")
            else None
        )

    async def async_demo(self) -> None:
        """Main routine to demonstrate the API code."""
        logging.basicConfig(level=logging.DEBUG)
        result = await self.async_connect()
        if result:
            self.session = {}
            for line in result.rstrip().split("\n"):
                key, value = line.strip().split(":")
                self.session[key] = value

        print("Demo GET_SCENES")
        # print(await self.async_process_command(GET_SCENES, sence_group=0))

        print("Demo SYN_DEVICE_STATUS with GET_DEVICE_NAMES")
        # data = await self.async_process_command(SYN_DEVICE_STATUS)
        # names = await self.async_process_command(GET_DEVICE_NAMES)
        # update_state_data(data, names)
        # print(data)

        print("Demo GET_ALL_EQUIPMENT_STATUS with GET_DEVICE_NAMES")
        data = await self.async_process_command(GET_ALL_EQUIPMENT_STATUS)
        names = await self.async_process_command(GET_DEVICE_NAMES)
        update_state_data(data, names)
        print(data)
        await self.async_disconnect()
        await asyncio.sleep(INTERVAL)
        update_nr = 0
        while update_nr < 0:
            try:
                update_nr += 1
                print(f"Demo status update {update_nr}...")
                # Start a new session
                await self.async_connect()
                status_update = await self.async_process_command(
                    GET_ALL_EQUIPMENT_STATUS
                )
                update_state_data(data, status_update)
                print(data)
                await asyncio.sleep(INTERVAL)
            except asyncio.exceptions.CancelledError as canceled_error:
                print(f"A cancelled error occcured! {canceled_error}")
                break
            except asyncio.exceptions.InvalidStateError as invalid_state_error:
                print(f"An invalid state error occcured! {invalid_state_error}")
            except asyncio.exceptions.TimeoutError as timeout_error:
                print(f"A timeout error occcured! {timeout_error}")
            finally:
                # Close the connection if needed
                await self.async_disconnect()
        # Test alarm (assuming there are 3 fire alarms)
        # Be aware they cannot be fired alle together, silence an alarm befor testing the next alarm.
        await self.async_connect()
        await self.async_process_command(TEST_ALARM, device_ID=1)
        await asyncio.sleep(4)
        await self.async_process_command(SILENCE_ALARM, device_ID=1)
        await self.async_process_command(TEST_ALARM, device_ID=2)
        await asyncio.sleep(4)
        await self.async_process_command(SILENCE_ALARM, device_ID=2)
        await self.async_process_command(TEST_ALARM, device_ID=3)
        await asyncio.sleep(4)
        await self.async_process_command(SILENCE_ALARM, device_ID=3)
        await self.async_disconnect()


if __name__ == "__main__":
    k1_hub = K1(sys.argv[1], sys.argv[2])
    asyncio.run(k1_hub.async_demo())
