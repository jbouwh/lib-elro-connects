"""Demo with login to the cloud."""

import asyncio
import sys

from elro.auth import ElroConnectsSession


class CloudDemo(ElroConnectsSession):
    """Demo with cloud login."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the demo."""
        self._username = username
        self._password = password
        ElroConnectsSession.__init__(self)

    async def async_login_demo(self) -> None:
        """Log in the user."""
        await self.async_login(self._username, self._password)
        print(f"user (id): {self.session['user']}")
        print(f"access_token: {self.session['access_token']}")
        print(f"last_login: {self.session['last_login']}")
        connector_list = await self.async_get_connectors()
        for connector in connector_list:
            print(connector["dev_id"])
            print(connector["sw_version"])
            print(connector["online"])


if __name__ == "__main__":
    # argv: 1 = email/username, 2 = password
    demo = CloudDemo(sys.argv[1], sys.argv[2])
    asyncio.run(demo.async_login_demo())
