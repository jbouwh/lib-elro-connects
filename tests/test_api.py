"""Test the elro connects API."""

import asyncio

from unittest.mock import MagicMock
import pytest

from elro.api import K1


@pytest.fixture
def k1_connector():
    """Mock a K1 connector."""
    asyncio.AbstractEventLoop.create_datagram_endpoint = MagicMock()
    asyncio.AbstractEventLoop.create_datagram_endpoint.return_value = (
        MagicMock(),
        MagicMock(),
    )
    yield K1("127.0.0.1", "ST_12345678")


@pytest.mark.asyncio
async def test_initialize_api(k1_connector):
    """Test the connection."""
    await k1_connector.async_connect()
    # await k1_connector.async_disconnect()
