"""Support communication with the Elro K1 hub."""

import logging
import json

import trio

from elro.command import Command
from elro.device import create_device_from_data
from elro.utils import get_string_from_ascii, get_ascii, crc_maker, get_eq_crc
from elro.validation import hostname, ip_address

_LOGGER = logging.getLogger(__name__)


class Hub:
    """
    A representation of the K1 Connector (its "Hub") of the Elro Connects system
    """

    APP_ID = "0"
    CTRL_KEY = "0"
    BIND_KEY = "0"

    def __init__(self, ip, port, device_id):
        """
        Constructor
        :param ip: The ip of the K1
        :param port: The port of the K1 (usually 1025)
        :param device_id: The device id of the K1 (starts with ST_ followed by its MAC address without colons)
        """
        self.ip = ip
        self.port = port
        self.id = device_id

        self.devices = {}
        self.unregistered_names = {}
        self.devices_for_sync = {}
        self.connected = False

        self.msg_id = 0
        self.sock = trio.socket.socket(trio.socket.AF_INET, trio.socket.SOCK_DGRAM)

        self.new_device_send_ch, self.new_device_receive_ch = trio.open_memory_channel(
            0
        )

    async def sender_task(self):
        """
        The main loop for sending keep alive messages asking for the current status to
        the K1
        """
        await self.connect()
        await self.sync_scenes(0)
        await self.get_device_names()

        _LOGGER.info("Waiting until all devices are retreived")
        await trio.sleep(5)
        if (
            len(self.devices_for_sync) > 0
        ):  # sync devices when there are devices known by name
            _LOGGER.info("Devices where replied, syncing those devices")
            await self.sync_device_status(self.devices_for_sync)

        # Main loop, keep updating every 30 seconds. Keeps 'connection' alive in order
        # to receive alarms/events
        while True:
            await trio.sleep(
                30
            )  # sleep first to handle the sync scenes and device names
            await self.sync_devices()
            await self.get_device_names()

    async def receiver_task(self):
        """
        The main loop for receiving data from the K1
        """
        while True:
            await self.receive_data()

    async def connect(self):
        """
        Connects with the K1
        """
        print("Start connection with hub.")
        while not self.connected:
            await self.send_data("IOT_KEY?" + self.id)
            await trio.sleep(1)

        await self.sync_device_status()

    def construct_message(self, data):
        """
        Construct a valid message from data
        :param data: A string containing data to be send to the K1
        :return: A json message
        """
        self.msg_id += 1

        result = (
            '{"msgId":'
            + str(self.msg_id)
            + ',"action":"appSend","params":{"devTid":"'
            + self.id
            + '","ctrlKey":"'
            + Hub.CTRL_KEY
            + '","appTid":"'
            + Hub.APP_ID
            + '","data":'
            + data
            + "}}"
        )
        return result

    async def send_data(self, data):
        """
        Sends data to the K1
        :param data: The data to be send
        """
        _LOGGER.info("Send data: %s", data)
        await self.sock.sendto(bytes(data, "utf-8"), (self.ip, self.port))

    async def receive_data(self):
        """
        Receives data from the K1
        """
        i = 0
        while i < 3:
            try:
                data = await self.sock.recv(4096)
                break
            except Exception as error:
                i = i + 1
                if i < 3:
                    _LOGGER.warning(
                        "Unable to connect to k1, retrying again. Error: %s", error
                    )
                    await trio.sleep(1)
                else:
                    _LOGGER.error("Unable to connect to k1 with error: %s", error)
                    exit()

        reply = str(data)[2:-1]
        if reply.endswith("\\n"):
            reply = reply[:-2]
        if reply.endswith("\\r"):
            reply = reply[:-2]

        _LOGGER.info("Received data: %s", reply)

        if f"NAME:{self.id}" in reply:
            for item in reply.split("\\n"):
                if "KEY" in item:
                    Hub.CTRL_KEY = item.split(":")[1]
                    _LOGGER.info("Got ctrlKey '%s'", Hub.CTRL_KEY)
                if "BIND" in item:
                    Hub.BIND_KEY = item.split(":")[1]
                    _LOGGER.info("Got bindKey '%s'", Hub.BIND_KEY)
            self.connected = True

        if reply.startswith("{") and reply != "{ST_answer_OK}":
            msg = json.loads(reply)
            dat = msg["params"]

            await self.handle_command(dat)

            # Send reply
            await self.send_data("APP_answer_OK")

    async def process_device(self, data):
        """
        Processes device, it will be added or removed accordingly
        :param data: The data of the device to process
        :return: The device object
        """
        _LOGGER.info("Process device with data: %s", data)
        d_id = data["data"]["device_ID"]
        if data["data"]["device_name"] == "DEL":
            await self.remove_device(data, False)
            return None
        else:
            dev = create_device_from_data(data)
            if dev is None:
                return None

            if self.unregistered_names.get(d_id):
                dev.name = self.unregistered_names[d_id]
                del self.unregistered_names[d_id]
            self.devices[d_id] = dev
            await self.new_device_send_ch.send(d_id)
            return self.devices[d_id]

    async def handle_command(self, data):
        """
        Handles all commands from the K1
        :param data: The data with the commands
        """
        _LOGGER.info("Handle command: %s", data)
        if data["data"]["cmdId"] == Command.DEVICE_STATUS_UPDATE.value:
            _LOGGER.debug("Processing cmdId: %s", data["data"]["cmdId"])
            if data["data"]["device_name"] == "STATUES":
                return

            # set device ID
            d_id = data["data"]["device_ID"]
            try:
                dev = self.devices[d_id]
            except KeyError:
                dev = await self.process_device(data)
            await trio.sleep(0)
            if dev is not None:
                dev.update(data)

        elif data["data"]["cmdId"] == Command.DEVICE_ALARM_TRIGGER.value:
            _LOGGER.debug("Processing cmdId: %s", data["data"]["cmdId"])
            d_id = int(data["data"]["answer_content"][6:10], 16)
            d_name = data["data"]["answer_content"][10:14]
            d_status = data["data"]["answer_content"][14:22]
            # Create the data object that is understood by all functions used below
            data = {
                "data": {
                    "cmdId": f"{Command.DEVICE_STATUS_UPDATE.value}",
                    "device_ID": d_id,
                    "device_name": f"{d_name}",
                    "device_status": f"{d_status}",
                }
            }

            try:
                dev = self.devices[d_id]
            except KeyError:
                _LOGGER.warning(
                    "Got device id '%s', but the device is not yet known. Trying to create the device",
                    d_id,
                )
                dev = await self.process_device(data)
                await trio.sleep(0)
                if dev is not None:
                    dev.update(data)

            dev.send_alarm_event(data)
            _LOGGER.debug("ALARM!! Device_id %s(%s)", d_id, dev.name)

        elif data["data"]["cmdId"] == Command.DEVICE_NAME_REPLY.value:
            _LOGGER.debug("Processing cmdId: %s", data["data"]["cmdId"])
            answer = data["data"]["answer_content"]
            if answer == "NAME_OVER":
                return

            d_id = int(answer[0:4], 16)
            name_val = get_string_from_ascii(answer[4:])

            # Build a list with known device names by device id
            try:
                dev = self.devices_for_sync[d_id]
            except KeyError:
                _LOGGER.info("Unknown name from device id '%s'", d_id)
                self.devices_for_sync[d_id] = "0464AA00"  # Bogus device status
                return
            await trio.sleep(0)

            # Set the device name from this reply
            try:
                dev = self.devices[d_id]
            except KeyError:
                self.unregistered_names[d_id] = name_val
                return
            await trio.sleep(0)
            dev.name = name_val

    async def sync_scenes(self, group_nr):
        """
        Sends a sync scene command to the K1
        :param group_nr: The scene group to sync
        """
        msg = self.construct_message(
            '{"cmdId":'
            + str(Command.SYN_SCENE.value)
            + ',"sence_group":'
            + str(group_nr)
            + ',"answer_content":"","scene_content":""}'
        )
        _LOGGER.info("sync scenes, group %s", group_nr)
        await self.send_data(msg)

    async def sync_devices(self):
        """
        Sends a sync devices command to the K1
        """
        msg = self.construct_message(
            '{"cmdId":'
            + str(Command.GET_ALL_EQUIPMENT_STATUS.value)
            + ',"device_status":""}'
        )
        _LOGGER.info("sync devices")
        await self.send_data(msg)

    async def get_device_names(self):
        """
        Sends a get device names command to the K1
        """
        msg = self.construct_message(
            '{"cmdId":' + str(Command.GET_DEVICE_NAME.value) + ',"device_ID":0}'
        )
        await self.send_data(msg)

    async def set_device_state(self, device_id, status):
        """
        Sets the device to the specified state
        :param device_id: The id of the device to change the state, 0 for all or the gateway(?)
        :param status: The status to set the device to
        """
        if (
            status == "00" and device_id == 0
        ):  # only allow the command silence for device id 0
            pass
        else:
            try:
                dev = self.devices[device_id]
            except KeyError:
                _LOGGER.error(
                    "Set device state device_id '%s' is not (yet) known", device_id
                )
                return

        data = (
            '{"cmdId":'
            + str(Command.EQUIPMENT_CONTROL.value)
            + ',"device_ID":'
            + str(device_id)
            + ',"device_status":"'
            + str(status)
            + '000000"}'
        )
        run = self.construct_message(data)
        _LOGGER.info("Set device '%s' state with: %s", device_id, run)
        await self.send_data(run)

    async def set_device_name(self, device_id, device_name):
        """
        Sets the device name
        :param device_id: The id of the device to change the name of
        :param device_name: The new name of the device
        """
        try:
            dev = self.devices[device_id]
        except KeyError:
            _LOGGER.error(
                "Set device name device_id '%s' is not (yet) known", device_id
            )
            return

        try:
            data = get_ascii(device_name)
        except Exception as error:
            _LOGGER.error(
                "Unable to set device_name for '%s' with error: %s",
                device_id,
                error,
            )
            return

        if len(data) == 0:
            _LOGGER.error(
                "Unable to set device_name for '%s', there is no hex string", device_id
            )
            return

        crc = crc_maker(data)
        datacrc = data + crc
        data = (
            '{"cmdId":'
            + str(Command.MODIFY_EQUIPMENT_NAME.value)
            + ',"device_ID":'
            + str(device_id)
            + ',"device_name":"'
            + str(datacrc)
            + '"}'
        )
        run = self.construct_message(data)
        _LOGGER.info(
            "Set device '%s' new name '%s' with: %s", device_id, device_name, run
        )
        await self.send_data(run)

    async def sync_device_status(self, devices=None):
        """
        Sends a sync device status command to the K1.
        :param devices: An dictionary of devices statuses, where the id of the device is the index of the dict
        """
        device_status = ""
        if devices is not None:
            device_status = get_eq_crc(devices)
        msg = self.construct_message(
            '{"cmdId":'
            + str(Command.SYN_DEVICE_STATUS.value)
            + ',"device_status":"'
            + device_status
            + '"}'
        )
        _LOGGER.info("sync device status with '%s'", msg)

        await self.send_data(msg)

    async def remove_device(self, device_id, from_hub=False):
        """
        Remove the device from the hub. This functions handles the delete from the hub, or the deleted devices are communicated by the hub
        :param device_id: The id of the device that will be removed
        :param from_hub: Also send the delete command to the hub
        """
        _LOGGER.info("Delete device '%s'", device_id)
        # Delete device
        try:
            dev = self.devices[device_id]
            del self.devices[device_id]
        except KeyError:
            pass
        except Exception as error:
            _LOGGER.error(
                "Unhandeld error when deleting device '%s': %s",
                device_id,
                error,
            )

        # Delete device from devices_for_sync
        try:
            dev = self.devices_for_sync[device_id]
            del self.devices_for_sync[device_id]
        except KeyError:
            pass
        except Exception as error:
            _LOGGER.error(
                "Unhandeld error when deleting device from the sync  '%s': %s",
                device_id,
                error,
            )

        # Delete device from devices_for_sync
        try:
            dev = self.unregistered_names[device_id]
            del self.unregistered_names[device_id]
        except KeyError:
            pass
        except Exception as error:
            _LOGGER.error(
                "Unhandeld error when deleting device from unregistered names  '%s': %s",
                device_id,
                error,
            )

        if from_hub:
            data = (
                '{"cmdId":'
                + str(Command.DELETE_EQUIPMENT.value)
                + ',"device_ID":'
                + str(device_id)
                + "}"
            )
            run = self.construct_message(data)
            _LOGGER.info("Delete device '%s' on the hub with: %s", device_id, run)
            await self.send_data(run)

    async def permit_join_device(self):
        """
        Enable the hub to add new devices
        """
        data = '{"cmdId":' + str(Command.INCREACE_EQUIPMENT.value) + "}"
        run = self.construct_message(data)
        _LOGGER.info("Permit join device with: %s", run)
        await self.send_data(run)

    async def permit_join_device_disable(self):
        """
        Disable the hub to join new devices
        """
        data = '{"cmdId":' + str(Command.CANCEL_INCREACE_EQUIPMENT.value) + "}"
        run = self.construct_message(data)
        _LOGGER.info("Disable join device with: %s", run)
        await self.send_data(run)

    async def replace_device(self, device_id):
        """
        Replace the specified device
        :param device_id: The id of the device that will be replaced
        """
        _LOGGER.info("Replace device '%s'", device_id)
        # Delete device
        try:
            dev = self.devices[device_id]
            del self.devices[device_id]
        except KeyError:
            _LOGGER.warning(
                "Cannot replace device. Device id '%s' does not exist.", device_id
            )
            return
        except Exception as error:
            _LOGGER.error(
                "Unhandeld error when replacing device  '%s': %s", device_id, error
            )

        data = '{"cmdId":' + str(Command.REPLACE_EQUIPMENT.value) + "}"
        run = self.construct_message(data)
        _LOGGER.info("Permit join device with: %s", run)
        await self.send_data(run)
