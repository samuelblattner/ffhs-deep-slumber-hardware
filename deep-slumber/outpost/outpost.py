import json

import time
from typing import List

from outpost.enum import MessageType
from outpost.interfaces import OutpostListener
from outpost.message import AbstractMessage, HelloMessage, Event, Settings
import websockets
import asyncio

from risenshine.risenshine import RiseNShine


class Outpost:

    HWID = 12345678

    __socket = None
    __message_queue: asyncio.Queue
    __main_loop = None
    listeners: List[OutpostListener]

    def __init__(self):
        self.__socket = None
        self.__message_queue = asyncio.Queue(maxsize=2**18)
        self.__main_loop = asyncio.get_event_loop()

    async def listen_for_messages(self):
        while True:
            raw_msg = await self.__socket.recv()
            self.onMessage(raw_msg)

    async def send_messages(self):
        while True:
            msg = await self.__message_queue.get()
            await self.__socket.send(msg.serialize())
            self.__message_queue.task_done()

    async def establish_socket(self):
        self.__socket = await websockets.connect('ws://192.168.1.41:8777')
        await self.__socket.send(HelloMessage(hwid=self.HWID).serialize())

    async def start_message_queues(self):
        consumer = asyncio.ensure_future(self.listen_for_messages())
        producer = asyncio.ensure_future(self.send_messages())
        done, pending = await asyncio.wait([
            consumer, producer
        ])

    def connect(self) -> bool:
        asyncio.get_event_loop().run_until_complete(self.establish_socket())
        asyncio.get_event_loop().run_until_complete(self.start_message_queues())
        return True

    def disconnect(self):
        pass

    def getSettings(self):
        return

    def registerListener(self, listener: OutpostListener):
        if listener not in self.listeners:
            self.listeners.append(listener)

    def send_message(self, msg: AbstractMessage):
        self.__main_loop.call_soon_threadsafe(self.__message_queue.put_nowait, msg)
        self.__main_loop.call_soon_threadsafe(lambda: print(self.__message_queue.qsize()))

    def digestSettings(self, settings: Settings):
        RiseNShine.setWakeTime(settings.wakeTime)

    def onMessage(self, raw: str):

        try:
            obj = json.loads(raw)
        except:
            return

        if MessageType(obj.get('msgType')) == MessageType.SETTINGS:
            self.digestSettings(Settings.deserialize(raw))

