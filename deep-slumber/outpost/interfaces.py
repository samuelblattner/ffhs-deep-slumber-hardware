from abc import ABCMeta

from outpost.message import AbstractMessage


class OutpostListener:

    __metaclass__ = ABCMeta

    def on_message(self, msg: AbstractMessage):
        raise NotImplementedError()
