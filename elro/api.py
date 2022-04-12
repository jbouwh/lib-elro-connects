"""Elro connects API."""

from __future__ import annotations

import asyncio
import json
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
)

ATTR_BIND = "BIND"
ATTR_KEY = "KEY"
ATTR_NAME = "NAME"

APP_ID = 0

TIMEOUT = 10
UDP_PORT_NO = 1025

# GET_DEVICE_NAMES returns a dict[{device_id}, {device_name}]
GET_DEVICE_NAMES = CommandAttributes(
    cmd_id=Command.GET_DEVICE_NAME,
    additional_attributes={"device_ID": 0},
    receive_types=[Command.DEVICE_NAME_REPLY],
    content_field="answer_content",
    content_sync_finished="NAME_OVER",
    content_transformer=get_device_names,
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
        self.datagram_data.done = True


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

    async def connect(self) -> str:
        """Connect to the K1 hub."""
        self.loop = asyncio.get_running_loop()
        on_conn_lost, datagram_data = (
            self.loop.create_future(),
            self.loop.create_future(),
        )
        payload = (CMD_CONNECT + self.k1_id).encode("utf-8")
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
                    self.protocol.datagram_data = self.loop.create_future()
                    print(raw_data[0].decode("utf-8").strip())
                    data = json.loads(raw_data[0].decode("utf-8"))
                    cmd_id = data["params"]["data"]["cmdId"]
                    content = data["params"]["data"].get(
                        attributes["content_field"], ""
                    )
                    if Command(cmd_id) in attributes["receive_types"]:
                        self.transport.sendto(ACK_APP.encode("utf-8"))
                        if content == attributes["content_sync_finished"]:
                            break
                        if content:
                            contentlist.append(content)

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

    async def async_main(self) -> None:
        """Main routine to demonstratie the API PoC."""
        result = await self.connect()
        if result:
            self.session = {}
            for line in result.rstrip().split("\n"):
                key, value = line.strip().split(":")
                self.session[key] = value

        print(await self.async_process_command(GET_SCENES, sence_group=0))
        print(await self.async_process_command(GET_DEVICE_NAMES))

        self.transport.close()


if __name__ == "__main__":
    k1_hub = K1(sys.argv[1], sys.argv[2])
    asyncio.run(k1_hub.async_main())
