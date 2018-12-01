from enum import Enum


class MessageType(Enum):
    SETTINGS = 1
    COMMAND = 2
    HEARTBEAT = 100


class EventType(Enum):
    START_REC = 1
    STOP_REC = 2
    PAUSE_REC = 3
    START_WAKING = 10
    USER_ABORT_WAKING = 11
    END_WAKING = 12
    MOVEMENT = 1000
    TEMPERATURE = 1001
    PRESSURE = 1002
    HUMIDITY = 1003
