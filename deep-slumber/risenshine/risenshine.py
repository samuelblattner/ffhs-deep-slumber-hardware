from threading import Thread, Event as ThreadEvent
from datetime import datetime, timedelta
import time

from logger.logger import Logger
from orchestra.orchestra import Orchestra
from outpost.enum import EventType
from outpost.message import Event
from risenshine.interfaces import WakingOperator


class WakeTimerThread(Thread):

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
        if waketime < datetime.now():
            waketime = waketime.replace(day=datetime.now().day + 1)
        return waketime

    def runWakeTimer(self, wakeTime):
        while not self.__abort_event.is_set():
            if datetime.now() > self.__wake_time:
                self.__wake_callback()
                self.__wake_time = WakeTimerThread.place_waketime_ahead(self.__wake_time)
            time.sleep(10)

    def run(self):
        self.runWakeTimer(self.__wake_time)

    def join(self, timeout=None):
        self.__abort_event.set()
        Thread.join(self, timeout)


class WakeThread(Thread):

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


class RiseNShine(WakingOperator):

    DEFAULT_WAKE_DURATION_MIN = 15

    __alarm_thread: Thread = None
    __wake_thread: Thread = None
    __orchestra: Orchestra = None
    __logger: Logger = None

    __latest_wake_time: datetime = None
    __earliest_wake_time: datetime = None

    def __init__(self, orchestra, logger):
        self.__orchestra = orchestra
        self.__logger = logger

    def set_waking_time(self, latest_wake_time, earliest_wake_time=None):
        """
        Sets wake time
        :param latest_wake_time:
        :param earliest_wake_time:
        :return:
        """

        if self.__alarm_thread is not None and self.__alarm_thread.is_alive():
            self.__alarm_thread.join()

        self.__earliest_wake_time = WakeTimerThread.place_waketime_ahead(earliest_wake_time)
        self.__latest_wake_time = WakeTimerThread.place_waketime_ahead(latest_wake_time)

        if latest_wake_time is not None:
            self.__alarm_thread = WakeTimerThread(
                wake_time=earliest_wake_time if earliest_wake_time else latest_wake_time - timedelta(minutes=self.DEFAULT_WAKE_DURATION_MIN),
                wake_callback=self.perform_waking
            )
            self.__alarm_thread.start()

    def perform_waking(self):
        if self.__wake_thread is None or not self.__wake_thread.is_alive():
            self.__wake_thread = WakeThread(
                wake_step_fn=self.__orchestra.set_wake_light_step,
                duration=(self.__latest_wake_time - self.__earliest_wake_time).seconds,
                logger=self.__logger
            )
            self.__wake_thread.start()
