"""
Logger module.

Collects and dispatches logging messages.
"""

__author__ = 'Samuel Blattner'
__version__ = '1.0.0'


from typing import List

from logger.interfaces import LogConsumer
from outpost.message import Event


class Logger:

    __consumers: List[LogConsumer] = []

    def __init__(self, consumers: List[LogConsumer]):
        self.__consumers = consumers

    def log_event(self, event: Event):
        """
        Log an event.
        Calls all consumers and passes the event to be logged.
        :param event: {Event} Event to be logged
        """
        for consumer in self.__consumers:
            consumer.consume_log_message(event)
