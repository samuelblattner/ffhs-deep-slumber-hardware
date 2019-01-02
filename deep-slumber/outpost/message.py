"""
Outpost messages module.

Message formats for server communication.
"""

__author__ = 'Samuel Blattner'
__version__ = '1.0.0'


from abc import ABCMeta
import json
from json import JSONDecodeError
from datetime import datetime
from typing import Optional

from outpost.enum import EventType, MessageType


class AbstractMessage:
    """
    Abstract Message class.
    Provides simple mechanism for serialization/deserialization
    """
    __metaclass__ = ABCMeta

    _fields = ()
    _msgType: MessageType

    @classmethod
    def deserialize(cls, raw: str) -> Optional:
        """
        Deserialize a given raw string into a message object.
        :param raw: {str} Serialized representation of the message
        :return: {AbstractMessage} Deserialized message object
        """
        try:
            data = json.loads(raw)
        except JSONDecodeError:
            return None

        instance = cls()
        for field_name in cls._fields:
            if hasattr(instance, field_name):
                setattr(instance, field_name, data.get(field_name))
        return instance

    def serialize(self) -> str:
        """
        Serialize this message object and return it as string.
        :return: {str} Serialized message object
        """
        out = {}
        for field in self._fields:
            if hasattr(self, field):
                out.setdefault(field, getattr(self, field))

        out.setdefault('msgType', self._msgType.value)
        return json.dumps(out)

    def get_message_type(self) -> MessageType:
        return self._msgType


class Settings(AbstractMessage):
    """
    Settings message containing user settings
    for waking/recording process.
    """
    _msgType = MessageType.SETTINGS

    earliestWakeTime = None
    latestWakeTime = None
    wakeMaxSpan = 0
    wakeOffsetEstimator = None
    accSensitivity = 0
    gyrSensitivity = 0
    irSensitivity = 0
    dataDensity = 1

    _fields = (
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
    """
    Events sent by hardware.
    """
    _msgType = MessageType.EVENT

    hwid: str
    event_type: EventType
    timestamp: datetime
    value = 0

    _fields = (
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
    """
    Initial message sent to server upon successful connection.
    """
    _fields = ('hwid',)

    _msgType = MessageType.HELLO
    hwid = -1

    def __init__(self, hwid):
        self.hwid = hwid
