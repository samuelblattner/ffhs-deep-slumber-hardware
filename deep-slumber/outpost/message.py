import json
from abc import ABCMeta, abstractmethod

from json import JSONDecodeError
import time
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

    earliestWakeTime = 0
    latestWakeTime = 0
    wakeMaxSpan = 0
    wakeOffsetEstimator = None
    accSensitivity = 0
    gyrSensitivity = 0
    irSensitivity = 0
    dataDensity = 1

    fields = (
        'earliestWakeTime',
        'latestWakeTime',
        'wakeMaxSpan',
        'wakeOffsetEstimator',
        'accSensitivity',
        'gyrSensitivity',
        'irSensitivity',
        'dataDensity',
    )

    @classmethod
    def deserialize(cls, raw: str):
        settings = super(Settings, cls).deserialize(raw)
        if settings.earliestWakeTime is not None:
            settings.earliestWakeTime = datetime.strptime(settings.earliestWakeTime.get('date'), '%Y-%m-%d %H:%M:%S.%f')
        if settings.latestWakeTime is not None:
            settings.latestWakeTime = datetime.strptime(settings.latestWakeTime.get('date'), '%Y-%m-%d %H:%M:%S.%f')

        return settings


class Event(AbstractMessage):
    _msgType = MessageType.EVENT

    hwid: str
    event_type: EventType
    timestamp: datetime
    value = 0

    fields = (
        'hwid',
        'event_type',
        'timestamp',
        'value'
    )

    def __init__(self, event_type: EventType.IGNORE, value=0):
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.value = value
        self.hwid = None

    def __str__(self):
        return 'Event {}@{}: {}'.format(self.event_type, self.timestamp, self.value)

    def serialize(self):
        j = json.dumps({
            'hwid': self.hwid,
            'msgType': self._msgType.value,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'value': self.value
        })
        return j


class HelloMessage(AbstractMessage):
    fields = ('hwid',)

    _msgType = MessageType.HELLO
    hwid = -1

    def __init__(self, hwid):
        self.hwid = hwid
