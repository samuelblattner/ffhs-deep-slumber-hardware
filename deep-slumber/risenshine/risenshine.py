"""
Rise N Shine Module.

Handles waking procedures.
"""


from threading import Thread
from datetime import datetime, timedelta

from logger.logger import Logger
from orchestra.orchestra import Orchestra
from outpost.enum import MessageType
from outpost.interfaces import OutpostListener
from outpost.message import AbstractMessage, Settings
from risenshine.waking import WakeTimerThread, WakeThread


class RiseNShine(OutpostListener):

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

    def set_decision_time(self, latest_wake_time, earliest_wake_time=None):
        """
        Set the decision time. When this time is reached, the system needs to decide
        when to start the waking process.
        :param latest_wake_time: {datetime} Latest wake-up time
        :param earliest_wake_time: {datetime} Earliest wake-up time
        """

        if self.__alarm_thread is not None and self.__alarm_thread.is_alive():
            self.__alarm_thread.join()

        self.__earliest_wake_time = WakeTimerThread.place_waketime_ahead(earliest_wake_time)
        self.__latest_wake_time = WakeTimerThread.place_waketime_ahead(latest_wake_time)

        if latest_wake_time is not None:
            self.__alarm_thread = WakeTimerThread(
                wake_time=earliest_wake_time if earliest_wake_time else latest_wake_time - timedelta(minutes=self.DEFAULT_WAKE_DURATION_MIN),
                wake_callback=self.on_decision_time
            )
            self.__alarm_thread.start()

    def on_decision_time(self):
        """
        Called when system needs to decide when to start the waking process.
        This is currently not yet implemented and the waking process is started immediately.
        """
        self.perform_waking()
        # TODO: Implement evaluation of waking process start based on trained ML model.

    def perform_waking(self):
        if self.__wake_thread is None or not self.__wake_thread.is_alive():
            self.__wake_thread = WakeThread(
                wake_step_fn=self.__orchestra.set_wake_light_step,
                duration=(self.__latest_wake_time - self.__earliest_wake_time).seconds,
                logger=self.__logger
            )
            self.__wake_thread.start()

    # =========================== ifOutpostListener Methods =============================
    def on_message(self, msg: AbstractMessage):
        """
        Handle incoming messages from server
        :param msg: {AbstractMessage} Message from server
        """
        if msg.get_message_type() == MessageType.SETTINGS:
            self.digest_settings(msg)

    def digest_settings(self, settings: Settings):
        """
        Forward waking-settings to waking operator.
        :param settings: {Settings} Settings received from the server.
        """
        self.set_decision_time(settings.latestWakeTime, settings.earliestWakeTime)
