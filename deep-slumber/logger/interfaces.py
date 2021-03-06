from abc import ABCMeta, abstractmethod


class LogConsumer:
    """
    A LogConsumer receives and processes logging messages
    in a specific way.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def consume_log_message(self, msg):
        raise NotImplementedError()
