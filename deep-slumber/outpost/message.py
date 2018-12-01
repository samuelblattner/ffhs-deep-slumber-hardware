import json
from abc import ABCMeta, abstractmethod

from json import JSONDecodeError
from typing import Optional

from outpost.enum import EventType


class AbstractMessage:

    __metaclass__ = ABCMeta

    fields = ()

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
    eventType: EventType
    timestamp: int
    value = 0