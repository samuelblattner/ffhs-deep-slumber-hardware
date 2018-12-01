from abc import ABCMeta, abstractmethod

from outpost.message import AbstractMessage


class OutpostListener:

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_message(self, msg: AbstractMessage):
        raise NotImplementedError()
