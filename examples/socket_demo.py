"""Socket demo test code."""

import asyncio
import sys
from datetime import datetime

from elro.api import K1
from elro.command import (
    GET_ALL_EQUIPMENT_STATUS,
    GET_DEVICE_NAMES,
    Command,
    CommandAttributes,
)
from elro.utils import get_device_states, update_state_data


class SocketDemo(K1):
    """Class to test Elro connects sockets."""

    async def async_show_status(self) -> None:
        """Main routine to demonstrate the API code."""
        # You can call await self.async_connect() but if there is no actice session
        # await self.async_connect() will be called for you

        await self.async_connect()
        try:
            data = await self.async_process_command(GET_ALL_EQUIPMENT_STATUS)
            names = await self.async_process_command(GET_DEVICE_NAMES)
            update_state_data(data, names)
            device_states = get_device_states(
                [device_data["device_status_data"] for _, device_data in data.items()]
            )
            print(f"=={datetime.now()}")
            for key, item in data.items():
                print(
                    f"{key} ({item.get('name')}): status={item['device_state']} data={item['device_status_data']}"
                )
                print(f"> {device_states[key]}")
        except Exception as err:  # pylint: disable=broad-except
            print(f"Exception caught {err.args}")
        await self.async_disconnect()

    async def async_test_socket(self, device_id: int, command_code_hex: str) -> None:
        """Test socket command."""
        # TEST_ALARM for fire alarms
        command = CommandAttributes(
            cmd_id=Command.EQUIPMENT_CONTROL,
            attribute_transformer=None,
            additional_attributes={
                "device_ID": 0,
                "device_status": f"{command_code_hex}000000",
            },
            receive_types=[Command.ANSWER_YES_OR_NO],
            content_field="answer_yes_or_no",
            content_sync_finished=2,
            content_transformer=None,
        )
        await self.async_connect()
        print(f"Send command {command_code_hex} to device with ID: {device_id}")
        await self.async_process_command(command, device_ID=device_id)
        await self.async_disconnect()
        await asyncio.sleep(4)
        await self.async_show_status()


if __name__ == "__main__":
    # argv: 1 = IP_ADDRESS, 2 = API_KEY, 3 = device_id
    ARG_DEVICE_ID = int(sys.argv.get[3]) if len(sys.argv) > 3 else None
    ARG_COMMAND_HEX = sys.argv[4] if len(sys.argv) > 4 else None
    k1_hub = SocketDemo(sys.argv[1], sys.argv[2])
    if ARG_COMMAND_HEX is not None:
        asyncio.run(k1_hub.async_test_socket(ARG_DEVICE_ID, ARG_COMMAND_HEX))
    else:
        asyncio.run(k1_hub.async_show_status())
