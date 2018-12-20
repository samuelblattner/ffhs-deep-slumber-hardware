from abc import ABCMeta, abstractmethod


class WakingOperator:

    __metaclass__ = ABCMeta

    @abstractmethod
    def set_waking_time(self, latest_wake_time, earliest_wake_time = None):
        raise NotImplementedError()

    @abstractmethod
    def perform_waking(self):
        raise NotImplementedError()
