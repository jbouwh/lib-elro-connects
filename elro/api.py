"""Elro connects API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Mapping, cast, Any, TypedDict

from elro.command import (
    Command,
    CommandAttributes,
    ACK_APP,
    CMD_CONNECT,
)
from elro.utils import (
    validate_json,
)

ATTR_BIND = "BIND"
ATTR_KEY = "KEY"
ATTR_NAME = "NAME"

APP_ID = 0

TIME_OUT = 10
INTERVAL = 5
UDP_PORT_NO = 1025

_LOGGER = logging.getLogger(__name__)


class K1UDPHandler(asyncio.BaseProtocol):
    """UDP test class."""

    def __init__(self, message, on_con_lost, datagram_data):
        self.message = message
        self.on_con_lost = on_con_lost
        self._transport = None
        self.datagram_data = datagram_data
        self.last_exc = None

    def connection_made(self, transport):
        """Connection made."""
        self._transport = transport
        self._transport.sendto(self.message)

    def datagram_received(self, data, addr):
        """Datagram reveived."""
        if not self.datagram_data.done():
            self.datagram_data.set_result((data, addr))

    def close_connection(self):
        """Close the connection."""
        self._transport.close()

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

    _lock = asyncio.Lock()
    _loop: asyncio.AbstractEventLoop | None = None

    class K1ConnectionError(Exception):
        """K1 exception class."""

        def __init__(self, message: str = "K1 connection error") -> None:
            self.message = message
            super().__init__(self.message)

    class Reponse(TypedDict):
        """API Response class"""

        received: int

    def __init__(
        self, ipaddress: str, k1_id: str, port: int = 1025, api_key: str | None = None
    ) -> None:
        """Initialize the module."""
        self._transport = None
        self._protocol = None
        self._remoteaddress = (ipaddress, port)
        self._k1_id = k1_id
        self._session: dict[str, str] = {}
        self._msg_id = 0
        self._api_key = api_key

    async def async_connect(self) -> None:
        """Connect to the K1 hub."""

        def _store_session(self, data: str) -> None:
            """Stores the session details."""
            if data:
                self._session = {}
                for line in data.rstrip().split("\n"):
                    key, value = line.strip().split(":")
                    self._session[key] = value
                # Allow to override the key if the connector is not providing the key or when the key is obtained from the cloud
                if self._api_key:
                    self._session[ATTR_KEY] = self._api_key

        self._loop = asyncio.get_running_loop()
        if not self._loop:
            return
        on_conn_lost, datagram_data = (
            self._loop.create_future(),
            self._loop.create_future(),
        )
        payload = (CMD_CONNECT + self._k1_id).encode("utf-8")
        await self._lock.acquire()
        try:
            self._transport, self._protocol = await self._loop.create_datagram_endpoint(  # type: ignore
                lambda: K1UDPHandler(payload, on_conn_lost, datagram_data),
                remote_addr=self._remoteaddress,
            )
            await asyncio.wait_for(datagram_data, TIME_OUT)
            if data := datagram_data.result():
                _store_session(self, data[0].decode("utf-8"))
                return
            raise K1.K1ConnectionError(
                "No data received, cannot connect to "
                f"hub {self._remoteaddress[0]} with id {self._k1_id}."
            )
        except (ValueError, asyncio.TimeoutError) as exception:
            raise K1.K1ConnectionError(
                "Not received the expected result, cannot connect to "
                f"hub {self._remoteaddress[0]} with id {self._k1_id}."
                f" {exception.args}"
            ) from exception
        finally:
            self._lock.release()

    async def async_disconnect(self) -> None:
        """Disconnect from the K1 hub."""
        if not self._protocol:
            return
        await self._lock.acquire()
        try:
            if self._transport and not self._protocol.on_con_lost.done():
                self._transport.close()
                self._transport = None
                self._protocol = None
                self._session = {}
        finally:
            self._lock.release()

    async def async_configure(
        self, ipaddress: str, port: int = 1025, api_key: str | None = None
    ) -> None:
        """Process updated settings."""
        try:
            await self._lock.acquire()
            if self._transport and not self._protocol.on_con_lost.done():
                self._transport.close()
        finally:
            self._transport = None
            self._protocol = None
            self._session = {}
            self._api_key = api_key
            self._remoteaddress = (ipaddress, port)
            self._lock.release()

    def _prepare_command(self, command_data: dict) -> bytes:
        """
        Construct a valid message from data
        :param data: A string containing data to be send to the K1
        :return: A json message
        """
        self._msg_id += 1

        command = {
            "msgId": self._msg_id,
            "action": "appSend",
            "params": {
                "devTid": self._session[ATTR_NAME],
                "ctrlKey": self._session[ATTR_KEY],
                "appTid": 1,
                "data": command_data,
            },
        }
        return json.dumps(command).encode("utf-8")

    async def async_process_command(
        self,
        attributes: CommandAttributes,
        **argv: int | str,
    ) -> dict[int, dict[str, Any]] | None:
        """Get device names."""
        if not self._session:
            await self.async_connect()
        await self._lock.acquire()
        iteration = 0
        if (
            not self._protocol
            or not self._transport
            or not self._loop
            or ATTR_KEY not in self._session
        ):
            self._lock.release()
            raise K1.K1ConnectionError(
                "Not connected to a K1 hub or incorrect API key."
            )

        if attributes["attribute_transformer"]:
            attributes["attribute_transformer"](argv)
        command_data = {
            "cmdId": attributes["cmd_id"].value,
        }
        command_data.update(attributes["additional_attributes"])
        if argv:
            command_data.update(cast(Mapping[str, Any], argv))
        command = self._prepare_command(command_data)
        contentlist = []
        try:
            self._protocol.datagram_data = self._loop.create_future()
            self._transport.sendto(command)
            while True:
                # Run loop until last item
                await asyncio.wait_for(self._protocol.datagram_data, TIME_OUT)
                if raw_data := self._protocol.datagram_data.result():
                    iteration += 1
                    _LOGGER.debug(
                        "command attributes: %s received[%s]: %s",
                        command_data,
                        iteration,
                        raw_data[0].decode("utf-8").strip()
                        if raw_data[0] is not None
                        else None,
                    )
                    self._protocol.datagram_data = self._loop.create_future()
                    data = validate_json(raw_data[0])
                    params = data["params"]
                    cmd_id = params["data"]["cmdId"]
                    content = params["data"].get(attributes["content_field"], "")
                    if Command(cmd_id) in attributes["receive_types"]:
                        self._transport.sendto(ACK_APP.encode("utf-8"))
                        if content == attributes["content_sync_finished"]:
                            break
                        contentlist.append(params["data"])

                else:
                    self._transport.sendto(ACK_APP.encode("utf-8"))
                    break
        except (ValueError, asyncio.TimeoutError, asyncio.CancelledError) as exception:
            self._session = {}
            raise K1.K1ConnectionError(
                "Not received the expected result, cannot connect to "
                f"hub {self._remoteaddress[0]} with id {self._k1_id}."
                f" {exception.args}"
            ) from exception
        finally:
            self._lock.release()
        return (
            attributes["content_transformer"](contentlist)
            if attributes["content_transformer"] is not None
            else None
        )

    @property
    def api_key(self) -> str | None:
        """Return the api key."""
        return self._session.get(ATTR_KEY, None)

    @property
    def bind_key(self) -> str | None:
        """Return the bind-key."""
        return self._session.get(ATTR_BIND, None)

    @property
    def connector_id(self) -> str | None:
        """Return the connector-id."""
        return self._session.get(ATTR_NAME, None)
