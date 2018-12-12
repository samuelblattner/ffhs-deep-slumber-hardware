from enum import Enum


class MessageType(Enum):
    HELLO = 1
    SETTINGS = 2
    COMMAND = 3
    EVENT = 4
    HEARTBEAT = 100


class EventType(Enum):
    IGNORE = 0
    START_REC = 1
    STOP_REC = 2
    PAUSE_REC = 3
    RESUME_REC = 4
    START_WAKING = 10
    USER_ABORT_WAKING = 11
    END_WAKING = 12
    MOVEMENT = 1000
    TEMPERATURE = 1001
    PRESSURE = 1002
    HUMIDITY = 1003
