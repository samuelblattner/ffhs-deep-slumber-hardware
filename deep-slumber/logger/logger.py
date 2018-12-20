from typing import List

from logger.interfaces import LogConsumer
from outpost.message import Event


class Logger:

    __consumers: List[LogConsumer] = []

    def __init__(self, consumers: List[LogConsumer]):
        self.__consumers = consumers

    def log_event(self, event: Event):
        for consumer in self.__consumers:
            consumer.consume_log_message(event)
