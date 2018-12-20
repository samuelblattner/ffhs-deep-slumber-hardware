from abc import ABCMeta, abstractmethod


class LogConsumer:

    __metaclass__ = ABCMeta

    @abstractmethod
    def consume_log_message(self, msg):
        raise NotImplementedError()
