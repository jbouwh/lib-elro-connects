"""Elro Connects cloud authentication."""

from __future__ import annotations
from datetime import datetime

from json import dumps
from dataclasses import dataclass
from typing import TypedDict

import aiohttp

CLIENT_TYPE = "APP"
PID = "01288154146"
URL_LOGIN = "https://uaa-openapi.hekreu.me/login"
URL_DEVICE_LIST = "https://user-openapi.hekreu.me/device"


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

        async with aiohttp.ClientSession(json_serialize=dumps) as session:
            async with session.post(URL_LOGIN, json=body, headers=headers) as resp:
                response = await resp.json()

        response["last_login"] = datetime.now()

        self._session_cache = ElroConnectsCloudSessionCache(**response)

    @property
    def session(self) -> ElroConnectsCloudSessionCache | None:
        """Return the current session."""
        return self._session_cache

    async def async_get_connectors(self) -> list[ElroConnectsConnector]:
        """Return as list of registered connectors."""

        if self._session_cache is None:
            raise ValueError("Cannot get connector list, no valid session")

        # Get the list
        headers = {
            "User-Agent": "lib-elro-connects",
            "Authorization": f"Bearer {self._session_cache['access_token']}",
        }

        async with aiohttp.ClientSession(json_serialize=dumps) as session:
            async with session.get(URL_DEVICE_LIST, headers=headers) as resp:
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
