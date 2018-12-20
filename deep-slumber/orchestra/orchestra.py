import threading

import asyncio
from RPi import GPIO
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from phue import Bridge
from sense_hat import SenseHat

from logger.logger import Logger
from orchestra.enums import OrchestraState
from outpost.enum import EventType
from outpost.message import Event, Settings


class Orchestra:

    GROUP = 2

    IR_SENSOR_PIN = 20
    READY_TO_IDLE_STATE_TIMEOUT = 3 * 60
    READY_TO_RECORDING_STATE_TIMEOUT = 10 * 60  # 10 minutes
    PAUSED_TO_IDLE_STATE_TIMEOUT = 10 * 60  # 10 minutes
    MOVEMENT_THREASHOLD = 0.05

    NUM_NORMALIZING_MOVEMENT_POLLS = 1

    MOVEMENT_POLL_INTERVAL = 1  # Every 5 seconds
    TEMPERATURE_POLL_INTERVAL = 10 * 60  # Every 10 minutes
    PRESURE_POLL_INTERVAL = 10 * 60  # Every 10 minutes
    HUMIDITY_POLL_INTERVAL = 10 * 60  # Every 10 minutes

    READY_TO_IDLE_STATE_TIMEOUT = 1 * 60
    READY_TO_RECORDING_STATE_TIMEOUT = 15  # 10 minutes
    PAUSED_TO_IDLE_STATE_TIMEOUT = 10 * 60  # 10 minutes

    MOVEMENT_THREASHOLD = 0.04

    MOVEMENT_POLL_INTERVAL = 1  # Every 5 seconds
    TEMPERATURE_POLL_INTERVAL = 10 * 60  # Every 10 minutes
    PRESURE_POLL_INTERVAL = 10 * 60  # Every 10 minutes
    HUMIDITY_POLL_INTERVAL = 10 * 60  # Every 10 minutes

    SENSEHAT_POLLING_STATE = {}
    SENSEHAT_POLLING = ({
                            'name': 'Temperature',
                            'polling_fn_name': 'get_temperature',
                            'handler_fn_name': 'on_temperature_signal',
                            'interval': TEMPERATURE_POLL_INTERVAL
                        }, {
                            'name': 'Pressure',
                            'polling_fn_name': 'get_pressure',
                            'handler_fn_name': 'on_pressure_signal',
                            'interval': PRESURE_POLL_INTERVAL
                        }, {
                            'name': 'Humidity',
                            'polling_fn_name': 'get_humidity',
                            'handler_fn_name': 'on_humidity_signal',
                            'interval': HUMIDITY_POLL_INTERVAL
                        }, {
                            'name': 'Movement',
                            'polling_fn_name': 'get_gyroscope_raw',
                            'handler_fn_name': 'on_movement_signal',
                            'interval': MOVEMENT_POLL_INTERVAL,
                            # 'diff_fn': lambda val: abs(val[1]['pitch'] - val[0]['pitch']) + abs(val[1]['roll'] - val[0]['roll']) + abs(val[1]['yaw'] - val[0]['yaw']) if val[0] is not None else 0
                            'diff_fn': lambda val: abs(val[1]['x'] - val[0]['x']) + abs(val[1]['y'] - val[0]['y']) + abs(val[1]['z'] - val[0]['z']) if val[
                                                                                                                                                           0] is not None else 0
                        },
    )

    __logger: Logger = None
    __settings: Settings = None

    __state: OrchestraState = OrchestraState.IDLE

    __sensehat: SenseHat = None
    __phue_bridge: Bridge = None

    __lastMovementTime: datetime = None
    __lastIRTime: datetime = None

    __ready_to_idle_state_timer = None
    __ready_to_ready_to_recording_timer = None
    __paused_to_idle_timer = None
    __normalizing_polls = 0
    __thread_pool_executor = None

    __loop = None

    def __init__(self, settings: Settings, logger: Logger):
        self.__loop = asyncio.get_event_loop()
        self.__logger = logger
        self.__settings = settings
        self.__set_up_IR()
        self.__thread_pool_executor = ThreadPoolExecutor()

        self.__set_up_sensehat()
        self.__phue_bridge = Bridge('192.168.1.129')

    def __activate_ready_to_idle_timeout(self):

        if self.__ready_to_idle_state_timer is not None:
            self.__cancel_ready_to_idle_timeout()
        self.__ready_to_idle_state_timer = threading.Timer(self.READY_TO_IDLE_STATE_TIMEOUT, self.__go_to_idle_state)
        self.__ready_to_idle_state_timer.start()

    def __cancel_ready_to_idle_timeout(self):
        if self.__ready_to_idle_state_timer is not None:
            self.__ready_to_idle_state_timer.cancel()
            self.__ready_to_idle_state_timer = None

    def __activate_paused_to_idle_timeout(self):
        if self.__paused_to_idle_timer is not None:
            self.__cancel_paused_to_idle_timeout()

        self.__paused_to_idle_timer = threading.Timer(self.PAUSED_TO_IDLE_STATE_TIMEOUT, self.__go_to_idle_state)
        self.__paused_to_idle_timer.start()

    def __cancel_paused_to_idle_timeout(self):
        if self.__paused_to_idle_timer is not None:
            self.__paused_to_idle_timer.cancel()
            self.__paused_to_idle_timer = None

    def __activate_ready_to_recording_timeout(self):
        if self.__ready_to_ready_to_recording_timer is None:
            self.__ready_to_ready_to_recording_timer = threading.Timer(self.READY_TO_RECORDING_STATE_TIMEOUT, self.__go_to_recording_state)
            self.__ready_to_ready_to_recording_timer.start()

    def __cancel_ready_to_recording_timeout(self):
        if self.__ready_to_ready_to_recording_timer is not None:
            self.__ready_to_ready_to_recording_timer.cancel()
            self.__ready_to_ready_to_recording_timer = None

    def __cancel_all_timeouts(self):
        self.__cancel_ready_to_idle_timeout()
        self.__cancel_ready_to_recording_timeout()

    def __set_up_IR(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.IR_SENSOR_PIN, GPIO.IN)
        GPIO.add_event_detect(self.IR_SENSOR_PIN, GPIO.BOTH, self.on_IR_signal)

    def __set_up_sensehat(self):
        self.__sensehat = SenseHat()
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        asyncio.get_event_loop().run_in_executor(self.__thread_pool_executor, self.__run_sensehat_polling)

    def __go_to_idle_state(self):
        self.__cancel_all_timeouts()

        if self.__state == OrchestraState.PAUSED:
            self.__logger.log_event(
                Event(
                    event_type=EventType.STOP_REC
                )
            )

        self.__logger.log_event(
            Event(
                event_type=EventType.STATE_CHANGE,
                value=OrchestraState.IDLE.value
            )
        )
        self.__state = OrchestraState.IDLE

    def __go_to_recording_state(self):
        if self.__state in (OrchestraState.READY, OrchestraState.PAUSED):
            self.__state = OrchestraState.RECORDING
            self.__phue_bridge.set_group(self.GROUP, {'on': False}, transitiontime=100)
            self.__logger.log_event(
                Event(event_type=EventType.START_REC)
            )

    def __go_to_paused_state(self):
        if self.__state == OrchestraState.RECORDING:
            self.__state = OrchestraState.PAUSED

    def __run_sensehat_polling(self):

        self.__normalizing_polls = 0
        while self.__state != OrchestraState.IDLE:

            for poll_info in self.SENSEHAT_POLLING:

                poll_name = poll_info.get('name')
                poll_fn = poll_info.get('polling_fn_name', None)
                handler_fn = poll_info.get('handler_fn_name', lambda x: x)
                diff_fn = poll_info.get('diff_fn', lambda x: 0)
                poll_interval = poll_info.get('interval')

                poll_state = self.SENSEHAT_POLLING_STATE.get(poll_name, {})
                last_poll_time = poll_state.get('last_poll', None)

                if poll_fn is not None and (last_poll_time is None or (datetime.now() - last_poll_time).seconds >= poll_interval):
                    old_val = poll_state.get('value', None)
                    new_val = getattr(self.__sensehat, poll_fn)()
                    poll_state['last_poll'] = datetime.now()

                    diff = 0
                    if diff_fn:
                        diff = diff_fn((old_val, new_val))

                    poll_state['value'] = new_val
                    if handler_fn:
                        getattr(self, handler_fn)(poll_state.get('value'), diff)

                    self.SENSEHAT_POLLING_STATE[poll_name] = poll_state

            time.sleep(2)

    def on_IR_signal(self, *args, **kwargs):

        # On, i.e. person present
        self.__lastIRTime = datetime.now()

        if GPIO.input(self.IR_SENSOR_PIN) == 1:

            if self.__state == OrchestraState.IDLE:

                self.__logger.log_event(
                    Event(
                        event_type=EventType.STATE_CHANGE,
                        value=OrchestraState.READY.value
                    )
                )
                self.__state = OrchestraState.READY
                self.__set_up_sensehat()
                self.__activate_ready_to_idle_timeout()

            elif self.__state == OrchestraState.RECORDING:

                self.__logger.log_event(
                    Event(
                        event_type=EventType.STATE_CHANGE,
                        value=OrchestraState.PAUSED.value
                    )
                )

                self.__state = OrchestraState.PAUSED
                self.__logger.log_event(
                    Event(
                        event_type=EventType.PAUSE_REC
                    )
                )
                self.__activate_paused_to_idle_timeout()

    def on_movement_signal(self, value, diff):

        if diff > self.MOVEMENT_THREASHOLD and self.__normalizing_polls > self.NUM_NORMALIZING_MOVEMENT_POLLS:

            # If there's movement, prevent the system from going into
            # idle mode.
            self.__cancel_ready_to_idle_timeout()

            if self.__state == OrchestraState.READY:
                self.__activate_ready_to_recording_timeout()

            elif self.__state == OrchestraState.RECORDING:
                if diff > self.MOVEMENT_THREASHOLD:
                    self.__logger.log_event(
                        Event(
                            event_type=EventType.MOVEMENT,
                            value=0
                        )
                    )
                    self.__logger.log_event(
                        Event(
                            event_type=EventType.MOVEMENT,
                            value=1
                        )
                    )
                    self.__logger.log_event(
                        Event(
                            event_type=EventType.MOVEMENT,
                            value=0
                        )
                    )
                    self.__normalizing_polls = 0

            elif self.__state == OrchestraState.PAUSED and (datetime.now() - self.__lastIRTime).seconds > 2:
                self.__state = OrchestraState.RECORDING
                self.__logger.log_event(
                    Event(
                        event_type=EventType.RESUME_REC
                    )
                )
                self.__cancel_paused_to_idle_timeout()
        else:
            self.__normalizing_polls += 1

    def on_temperature_signal(self, value, diff):
        if self.__state == OrchestraState.RECORDING:
            self.__logger.log_event(
                Event(
                    event_type=EventType.TEMPERATURE,
                    value=value
                )
            )

    def on_pressure_signal(self, value, diff):
        if self.__state == OrchestraState.RECORDING:
            self.__logger.log_event(
                Event(
                    event_type=EventType.PRESSURE,
                    value=value
                )
            )

    def on_humidity_signal(self, value, diff):
        if self.__state == OrchestraState.RECORDING:
            self.__logger.log_event(
                Event(
                    event_type=EventType.HUMIDITY,
                    value=value
                )
            )

    def set_wake_light_step(self, step: float):
        self.__phue_bridge.set_group(self.GROUP, {'on': True, 'bri': min(int(255 * step), 255)}, transitiontime=10)

    def __del__(self):
        GPIO.cleanup()
