"""Elro Connects cloud authentication."""

from __future__ import annotations
import asyncio
from datetime import datetime
from json import dumps
from dataclasses import dataclass
from typing import TypedDict


import socket
import json
import logging
import aiohttp


CLIENT_TYPE = "APP"
PID = "01288154146"
BASE_UAA_URL = "https://uaa-openapi."
BASE_USER_URL = "https://user-openapi."
DEFAULT_DOMAIN = "hekr.me"

_LOGGER = logging.getLogger(__name__)


@dataclass
class ElroConnectsCloudSessionCache(TypedDict):
    """Elro Connects cloud session cache."""

    access_token: str
    refresh_token: str
    expires_in: int
    last_login: datetime
    token_type: str
    user: int


@dataclass
class ElroConnectsConnector(TypedDict):
    """Elro Connects connector device."""

    dev_id: str
    ctrl_key: str
    bind_key: str
    mac: str
    data_center: str
    data_center_area: str
    sw_version: str
    model: str
    online: bool


class ElroConnectsSession:
    """Elro Connects Cloud session."""

    def __init__(self) -> None:
        """Initialize."""
        self._session_cache = None
        self._domain = None

    async def async_login(
        self, username: str, password: str
    ) -> ElroConnectsCloudSessionCache:
        """Login user and obtain a bearer token."""
        body = {
            "pid": PID,
            "username": username,
            "password": password,
            "clientType": CLIENT_TYPE,
        }
        headers = {
            "User-Agent": "lib-elro-connects",
        }
        domain = await self._async_get_domain()
        async with aiohttp.ClientSession(json_serialize=dumps) as session:
            async with session.post(
                BASE_UAA_URL + domain + "/login",
                json=body,
                headers=headers,
            ) as resp:
                response = await resp.json()

        response["last_login"] = datetime.now()

        self._session_cache = ElroConnectsCloudSessionCache(**response)

    @property
    def session(self) -> ElroConnectsCloudSessionCache | None:
        """Return the current session."""
        return self._session_cache

    async def _async_get_domain(self) -> str:
        """Return the API main domain name address."""

        def _get_domain() -> str | None:
            # domain has not been determined
            sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host = "info.hekr.me"
            port = 91
            sckt.connect((host, port))
            message = '{"action":"getAppDomain"}\n'
            sckt.send(message.encode())
            msg = sckt.recv(1024)

            try:
                parsed_data = json.loads(msg)
                _LOGGER.debug(
                    "%s result code: %s description: %s",
                    host,
                    parsed_data["code"],
                    parsed_data["desc"],
                )

                if "dcInfo" in parsed_data:
                    self._domain = parsed_data["dcInfo"]["domain"]
            except json.decoder.JSONDecodeError:
                return DEFAULT_DOMAIN

            if not self._domain.startswith("hekr"):  # default
                self._domain = None
                return DEFAULT_DOMAIN

            return self._domain

        # Only run once
        if self._domain:
            return self._domain

        loop = asyncio.get_event_loop()
        if domain := await loop.run_in_executor(None, _get_domain):
            self._domain = domain
        return domain

    async def async_get_connectors(self) -> list[ElroConnectsConnector]:
        """Return as list of registered connectors."""

        if self._session_cache is None:
            raise ValueError("Cannot get connector list, no valid session")

        # Get the list
        headers = {
            "User-Agent": "lib-elro-connects",
            "Authorization": f"Bearer {self._session_cache['access_token']}",
        }

        domain = await self._async_get_domain()
        async with aiohttp.ClientSession(json_serialize=dumps) as session:
            async with session.get(
                BASE_USER_URL + domain + "/device",
                headers=headers,
            ) as resp:
                response = await resp.json()
        connector_list = [
            ElroConnectsConnector(
                dev_id=connector["devTid"],
                ctrl_key=connector["ctrlKey"],
                bind_key=connector["bindKey"],
                mac=connector["mac"],
                data_center=connector["dcInfo"]["fromDC"],
                data_center_area=connector["dcInfo"]["fromArea"],
                sw_version=connector["binVersion"],
                model=connector["model"],
                online=connector["online"],
            )
            for connector in response
        ]

        return connector_list
