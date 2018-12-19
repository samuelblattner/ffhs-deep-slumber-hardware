from threading import Thread, Event

import time

import sched


class WakeTimerThread(Thread):

    __alarm_timeout = None
    __abort_event: Event = Event()
    __scheduler = None
    __wake_callback = None
    __wake_time = None

    def __init__(self, wake_time, wake_callback, *args, **kwargs):
        super(WakeTimerThread, self).__init__(*args, **kwargs)
        self.__wake_callback = wake_callback
        self.__wake_time = wake_time

    def runWakeTimer(self, wakeTime):
        self.__scheduler = sched.scheduler(time.time, time.sleep)
        print('setting time to ', wakeTime)
        self.__alarm_timeout = self.__scheduler.enterabs(wakeTime.timestamp(), 1, self.__wake_callback, argument=())
        self.__scheduler.run()
        print(time.time())
        print(wakeTime.timestamp())
        print('set')

    def run(self):
        self.runWakeTimer(self.__wake_time)

    def set_wake_time(self, wake_time):


    def join(self, timeout=None):
        self.__abort_event.set()
        print('aborting existing')
        if self.__alarm_timeout is not None:
            print('aborting existing 2')
            self.__scheduler.cancel(self.__alarm_timeout)
            self.__alarm_timeout = None
            print('cancelled')

        Thread.join(self, timeout)


class RiseNShine:

    __alarm_thread: Thread = None

    @classmethod
    def setWakeTime(cls, wakeTime):

        if cls.__alarm_thread is not None and cls.__alarm_thread.is_alive():
            cls.__alarm_thread.join()
            print('after join')

        print('creating new thread')
        cls.__alarm_thread = WakeTimerThread(wakeTime, cls.performWaking)
        cls.__alarm_thread.start()
        print('started')

    @classmethod
    def performWaking(self):
        print('WAKEY WAKEY :-)')

