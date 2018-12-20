import json

from typing import List
from websockets import ConnectionClosed
import time
from logger.interfaces import LogConsumer
from outpost.enum import MessageType
from outpost.interfaces import OutpostListener
from outpost.message import HelloMessage, Settings
import websockets
import asyncio

from risenshine.interfaces import WakingOperator


class Outpost(LogConsumer):

    def consume_log_message(self, msg):
        msg.hwid = self.HWID
        self.__main_loop.call_soon_threadsafe(self.__message_queue.put_nowait, msg)

    HWID = '7c222fb2927d828af22f592134e89324'

    __socket = None
    __message_queue: asyncio.Queue
    __main_loop = None
    __waking_operator: WakingOperator = None
    listeners: List[OutpostListener]

    def __init__(self):
        self.__socket = None
        self.__message_queue = asyncio.Queue(maxsize=2**18)
        self.__main_loop = asyncio.get_event_loop()

    def set_waking_oerator(self, waking_operator: WakingOperator):
        self.__waking_operator = waking_operator

    async def listen_for_messages(self):
        while True:
            try:
                raw_msg = await self.__socket.recv()
            except ConnectionClosed:
                self.__main_loop.call_soon_threadsafe(self.__message_queue.put_nowait, 'CONNECTION_FAILED')
                return
            self.onMessage(raw_msg)

    async def send_messages(self):
        while True:
            msg = await self.__message_queue.get()
            if msg == 'CONNECTION_FAILED':
                return
            try:
                await self.__socket.send(msg.serialize())
            except ConnectionClosed:
                return
            self.__message_queue.task_done()

    async def establish_socket(self):
        try:
            # self.__socket = await websockets.connect('ws://deep-slumber.samuelblattner.ch:8777')
            self.__socket = await websockets.connect('ws://192.168.1.2:8777')
        except ConnectionRefusedError:
            self.__socket = None
            return

        await self.__socket.send(HelloMessage(hwid=self.HWID).serialize())

    async def start_message_queues(self):
        consumer = asyncio.ensure_future(self.listen_for_messages())
        producer = asyncio.ensure_future(self.send_messages())
        await asyncio.wait([consumer, producer])

    def connect(self) -> bool:
        while True:
            asyncio.get_event_loop().run_until_complete(self.establish_socket())
            if self.__socket:
                asyncio.get_event_loop().run_until_complete(self.start_message_queues())

            time.sleep(10)
        return True

    def disconnect(self):
        pass

    def getSettings(self):
        return

    def registerListener(self, listener: OutpostListener):
        if listener not in self.listeners:
            self.listeners.append(listener)

    def digestSettings(self, settings: Settings):
        self.__waking_operator.set_waking_time(settings.latestWakeTime, settings.earliestWakeTime)

    def onMessage(self, raw: str):

        try:
            obj = json.loads(raw)
        except:
            return

        if MessageType(obj.get('msgType')) == MessageType.SETTINGS:
            self.digestSettings(Settings.deserialize(raw))
