#!/usr/bin/env python3

import logging
import argparse

import trio
import re

from getmac import get_mac_address

from elro.hub import Hub
from elro.mqtt import MQTTPublisher


async def main(hostname, hub_id, mqtt_broker, ha_autodiscover, base_topic):
    """Startup of CLI aplication."""
    hub = Hub(hostname, 1025, hub_id)
    hub.init_socket()
    mqtt_publisher = MQTTPublisher(mqtt_broker, ha_autodiscover, base_topic)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(mqtt_publisher.handle_hub_events, hub, name="hub_events")
        nursery.start_soon(hub.sender_task, name="hub_sender")
        nursery.start_soon(hub.receiver_task, name="hub_receiver")


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)-8s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    parser = argparse.ArgumentParser()
    parser._action_groups.pop()
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    required.add_argument(
        "-k", "--hostname", help="The hostname or ip of the K1 connector."
    )
    required.add_argument("-m", "--mqtt-broker", help="The IP of the MQTT broker.")
    required.add_argument(
        "-b", "--base-topic", help="The base topic of the MQTT topic.", default=None
    )
    optional.add_argument(
        "-i",
        "--id",
        help="The ID of the K1 connector (format is ST_xxxxxxxxxxxx).",
        default=None,
    )
    optional.add_argument(
        "-a",
        "--ha-autodiscover",
        help="Send the devices automatically to Home Assistant.",
        action="store_true",
    )

    args = parser.parse_args()

    k1id = args.id
    if k1id == None:
        mac = None
        if re.search(args.ip_address, args.hostname):
            mac = get_mac_address(ip=f"{args.hostname}")
        else:
            mac = get_mac_address(hostname=f"{args.hostname}")

        if mac is not None:
            k1id = f"ST_{(mac.replace(':',''))}"
            logging.info(f"Found k1 id '{k1id}' for hostname '{args.hostname}'")
        else:
            logging.error(
                f"Unable to determine k1 id '{k1id}' for hostname '{args.hostname}'. If the error persists, please provide --id as parameter"
            )
            quit()

    trio.run(
        main,
        args.hostname,
        k1id,
        args.mqtt_broker,
        args.ha_autodiscover,
        args.base_topic,
    )
