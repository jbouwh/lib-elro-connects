"""Command constants and classes."""

from __future__ import annotations
from enum import Enum
from typing import TypedDict, Callable

from elro.utils import (
    get_default,
    get_device_names,
    set_device_name,
    get_device_states,
)

COUNT = "count"
ACK_APP = "APP_answer_OK"

SCENE_SYNC_FINISHED = "OVER"
NAME_SYNC_FINISHED = "NAME_OVER"

CMD_CONNECT = "IOT_KEY?"


class Command(Enum):
    """
    ELRO Connects send commands copied from decompiled android app
    """

    SWITCH_TIMER = -34
    DELETE_EQUIPMENT_DETAIL = -4
    EQUIPMENT_CONTROL = 1
    INCREACE_EQUIPMENT = 2
    REPLACE_EQUIPMENT = 3
    DELETE_EQUIPMENT = 4
    MODIFY_EQUIPMENT_NAME = 5
    CHOOSE_SCENE_GROUP = 6
    CANCEL_INCREACE_EQUIPMENT = 7
    INCREACE_SCENE = 8
    MODIFY_SCENE = 9
    DELETE_SCENE = 10
    GET_DEVICE_NAME = 14
    GET_ALL_EQUIPMENT_STATUS = 15
    GET_ALL_SCENE_INFO = 18
    TIME_CHECK = 21
    INCREACE_SCENE_GROUP = 23
    MODIFY_SCENE_GROUP = 24
    SYN_DEVICE_STATUS = 29
    SYN_DEVICE_NAME = 30
    SYN_SCENE = 31
    SCENE_HANDLE = 32
    SCENE_GROUP_DELETE = 33
    MODEL_SWITCH_TIMER = 34
    MODEL_TIMER_SYN = 35
    UPLOAD_MODEL_TIMER = 36
    MODEL_TIMER_DEL = 37
    SEND_TIMEZONE = 251

    ANSWER_YES_OR_NO = 11

    # ELRO Connects receive commands
    # Reverse engineered
    DEVICE_STATUS_UPDATE = 19
    DEVICE_ALARM_TRIGGER = 25
    SCENE_STATUS_UPDATE = 26
    DEVICE_NAME_REPLY = 17

    SENCE_GROUP_DETAIL = 26
    SCENE_TYPE = 27
    SENCE_GROUP = 28


class CommandAttributes(TypedDict):
    """Base class for building command attributes for elro.api.async_process_command."""

    cmd_id: Command
    additional_attributes: dict
    attribute_transformer: Callable | None
    receive_types: list[Command]
    content_field: str
    content_sync_finished: int | str | None
    content_transformer: Callable | None


# GET_DEVICE_NAMES returns a dict[{device_id}, {device_name}]
GET_DEVICE_NAMES = CommandAttributes(
    cmd_id=Command.GET_DEVICE_NAME,
    attribute_transformer=None,
    additional_attributes={"device_ID": 0},
    receive_types=[Command.DEVICE_NAME_REPLY],
    content_field="answer_content",
    content_sync_finished="NAME_OVER",
    content_transformer=get_device_names,
)

# SET_DEVICE_NAMES returns a dict[{device_id}, {device_name}]
SET_DEVICE_NAME = CommandAttributes(
    cmd_id=Command.MODIFY_EQUIPMENT_NAME,
    attribute_transformer=set_device_name,
    additional_attributes={"device_ID": 0, "device_name": ""},
    receive_types=[Command.ANSWER_YES_OR_NO],
    content_field="answer_yes_or_no",
    content_sync_finished=2,
    content_transformer=None,
)

# SYN DEVICE_STATUS
SYN_DEVICE_STATUS = CommandAttributes(
    cmd_id=Command.SYN_DEVICE_STATUS,
    attribute_transformer=None,
    additional_attributes={"device_status": ""},
    receive_types=[Command.DEVICE_STATUS_UPDATE, Command.DEVICE_ALARM_TRIGGER],
    content_field="device_status",
    content_sync_finished="OVER",
    content_transformer=get_device_states,
)

# GET_ALL_EQUIPMENT_STATUS
GET_ALL_EQUIPMENT_STATUS = CommandAttributes(
    cmd_id=Command.GET_ALL_EQUIPMENT_STATUS,
    attribute_transformer=None,
    additional_attributes={"device_status": ""},
    receive_types=[Command.DEVICE_STATUS_UPDATE, Command.DEVICE_ALARM_TRIGGER],
    content_field="device_status",
    content_sync_finished="OVER",
    content_transformer=get_device_states,
)

# TEST_ALARM for fire alarms
TEST_ALARM = CommandAttributes(
    cmd_id=Command.EQUIPMENT_CONTROL,
    attribute_transformer=None,
    additional_attributes={"device_ID": 0, "device_status": "17000000"},
    receive_types=[Command.ANSWER_YES_OR_NO],
    content_field="answer_yes_or_no",
    content_sync_finished=2,
    content_transformer=None,
)
# TEST_ALARM_ALT for other detectors
TEST_ALARM_ALT = CommandAttributes(
    cmd_id=Command.EQUIPMENT_CONTROL,
    attribute_transformer=None,
    additional_attributes={"device_ID": 0, "device_status": "BB000000"},
    receive_types=[Command.ANSWER_YES_OR_NO],
    content_field="answer_yes_or_no",
    content_sync_finished=2,
    content_transformer=None,
)

SILENCE_ALARM = CommandAttributes(
    cmd_id=Command.EQUIPMENT_CONTROL,
    attribute_transformer=None,
    additional_attributes={"device_ID": 0, "device_status": "00000000"},
    receive_types=[Command.ANSWER_YES_OR_NO],
    content_field="answer_yes_or_no",
    content_sync_finished=2,
    content_transformer=None,
)

# GET_SCENES returns a dict[{scene_id}, None]
# NOTE: If queried frequently not all data is provisioned all the time
GET_SCENES = CommandAttributes(
    cmd_id=Command.SYN_SCENE,
    attribute_transformer=None,
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
