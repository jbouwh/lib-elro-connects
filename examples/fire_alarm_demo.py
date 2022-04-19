"""Example code to demonstrate the elro connects PI API with a firealarms."""

import asyncio
import logging
import sys

from elro.api import K1
from elro.command import (
    GET_SCENES,
    SYN_DEVICE_STATUS,
    GET_DEVICE_NAMES,
    GET_ALL_EQUIPMENT_STATUS,
    TEST_ALARM,
    SILENCE_ALARM,
)
from elro.utils import update_state_data

INTERVAL = 5


class AlarmDemo(K1):
    """Class to demonstrate Elro connects fire alarms."""

    async def async_demo(self) -> None:
        """Main routine to demonstrate the API code."""
        logging.basicConfig(level=logging.INFO)
        await self.async_connect()

        print("Demo GET_SCENES")
        print(await self.async_process_command(GET_SCENES, sence_group=0))

        print("Demo SYN_DEVICE_STATUS with GET_DEVICE_NAMES")
        data = await self.async_process_command(SYN_DEVICE_STATUS)
        names = await self.async_process_command(GET_DEVICE_NAMES)
        update_state_data(data, names)
        print(data)

        print("Demo GET_ALL_EQUIPMENT_STATUS with GET_DEVICE_NAMES")
        data = await self.async_process_command(GET_ALL_EQUIPMENT_STATUS)
        names = await self.async_process_command(GET_DEVICE_NAMES)
        update_state_data(data, names)
        print(data)
        await self.async_disconnect()
        await asyncio.sleep(INTERVAL)
        update_nr = 0
        while update_nr < 2:
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
        print("Test alarm 1")
        await self.async_process_command(TEST_ALARM, device_ID=1)
        await asyncio.sleep(4)
        print("Test alarm 2")
        await self.async_process_command(SILENCE_ALARM, device_ID=1)
        await self.async_process_command(TEST_ALARM, device_ID=2)
        await asyncio.sleep(4)
        print("Test alarm 3")
        await self.async_process_command(SILENCE_ALARM, device_ID=2)
        await self.async_process_command(TEST_ALARM, device_ID=3)
        await asyncio.sleep(4)
        await self.async_process_command(SILENCE_ALARM, device_ID=3)
        await self.async_disconnect()
        print("Demo completed")


if __name__ == "__main__":
    k1_hub = AlarmDemo(sys.argv[1], sys.argv[2])
    asyncio.run(k1_hub.async_demo())
