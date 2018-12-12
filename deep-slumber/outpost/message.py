import json
from abc import ABCMeta, abstractmethod

from json import JSONDecodeError

from datetime import datetime
from typing import Optional

from outpost.enum import EventType, MessageType


class AbstractMessage:

    __metaclass__ = ABCMeta

    fields = ()
    _msgType: MessageType

    def serialize(self) -> str:
        out = {}
        for field in self.fields:
            if hasattr(self, field):
                out.setdefault(field, getattr(self, field))

        out.setdefault('msgType', self._msgType.value)
        return json.dumps(out)

    @classmethod
    def deserialize(cls, raw: str) -> Optional:

        try:
            data = json.loads(raw)
        except JSONDecodeError:
            return None

        instance = cls()
        for field_name in cls.fields:
            if hasattr(instance, field_name):
                setattr(instance, field_name, data.get(field_name))

        return instance


class Settings(AbstractMessage):

    msgType = MessageType.SETTINGS

    wakeTime = 0
    wakeMaxSpan = 0
    wakeOffsetEstimator = None
    accSensitivity = 0
    gyrSensitivity = 0
    irSensitivity = 0
    dataDensity = 1

    @staticmethod
    def deserialize(raw: str):
        return Settings()


class Event(AbstractMessage):

    _msgType = MessageType.EVENT

    event_type: EventType
    timestamp: int
    value = 0

    def __init__(self, event_type: EventType.IGNORE, value=0):
        self.timestamp = datetime.now()
        self.event_type = event_type

    def __str__(self):
        return 'Event {}@{}: {}'.format(self.event_type, self.timestamp, self.value)


class HelloMessage(AbstractMessage):

    fields = ('hwid',)

    _msgType = MessageType.HELLO
    hwid = -1

    def __init__(self, hwid):
        self.hwid = hwid