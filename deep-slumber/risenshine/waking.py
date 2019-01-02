from threading import Thread, Event as ThreadEvent
from datetime import datetime
import time

from outpost.enum import EventType
from outpost.message import Event


class WakeTimerThread(Thread):
    """
    Special Thread to handle waking.
    """

    __abort_event: ThreadEvent
    __wake_callback = None
    __wake_time: datetime = None

    def __init__(self, wake_time, wake_callback, *args, **kwargs):
        super(WakeTimerThread, self).__init__(*args, **kwargs)
        self.__wake_callback = wake_callback
        self.__wake_time = wake_time
        self.__abort_event = ThreadEvent()
        self.__wake_time = WakeTimerThread.place_waketime_ahead(self.__wake_time)

    @staticmethod
    def place_waketime_ahead(waketime: datetime):
        """
        Re-schedule a given waking datetime in the future if it's
        before now().
        :param waketime: {datetime} Waking time to be re-scheduled.
        """
        if waketime is None:
            return waketime
        if waketime < datetime.now():
            waketime = waketime.replace(day=datetime.now().day + 1)
        return waketime

    def runWakeTimer(self, wakeTime):
        """
        Main timer loop.
        :param wakeTime:
        """
        while not self.__abort_event.is_set():
            if datetime.now() > self.__wake_time:
                self.__wake_callback()
                self.__wake_time = WakeTimerThread.place_waketime_ahead(self.__wake_time)
            time.sleep(1)

    def run(self):
        self.runWakeTimer(self.__wake_time)

    def join(self, timeout=None):
        self.__abort_event.set()
        Thread.join(self, timeout)


class WakeThread(Thread):
    """
    Special thread to run the waking process.
    """

    __wake_step = 0.0
    __wake_step_fn = None
    __logger = None
    __duration = 0

    def __init__(self, wake_step_fn, duration, logger, *args, **kwargs):
        self.__wake_step_fn = wake_step_fn
        self.__logger = logger
        self.__duration = duration
        super(WakeThread, self).__init__(*args, **kwargs)

    def run(self):

        self.__logger.log_event(
            Event(
                EventType.START_WAKING
            )
        )

        step_size_per_second = 1.0 / self.__duration

        while self.__wake_step < 1.0:
            self.__wake_step += step_size_per_second
            self.__wake_step_fn(self.__wake_step)

            time.sleep(1)

        self.__logger.log_event(
            Event(
                EventType.END_WAKING
            )
        )
