from outpost.message import Event
from outpost.outpost import Outpost


class Logger:

    __outpost: Outpost = None

    def __init__(self, outpost: Outpost):
        self.__outpost = outpost

    def log_event(self, event: Event):
        print('Logging Event: {}'.format(event))
        self.__outpost.send_message(event)
