"""
Outpost module.

This module establishes a Websocket-Connection to the Deep-Slumber server and
handles all communication from and to the server.
"""

__author__ = 'Samuel Blattner'
__version__ = '1.0.0'


import asyncio
import json
from json import JSONDecodeError
import time
from typing import List, Dict
import websockets
from websockets import ConnectionClosed

from logger.interfaces import LogConsumer
from outpost.enum import MessageType
from outpost.message import HelloMessage, Settings, AbstractMessage
from outpost.interfaces import OutpostListener


class Outpost(LogConsumer):

    # Statics
    __CONNECTION_FAIL_HOLDOFF_TIME = 10

    __SERVER_ADDRESS = 'ws://192.168.1.2:8777'
    # __SERVER_ADDRESS = 'wss://deep-slumber.samuelblattner.ch:8777'

    __HWID = '7c222fb2927d828af22f592134e89324'

    # Resources
    __socket = None
    __message_queue: asyncio.Queue
    __main_loop = None

    # Messaging
    __listeners: Dict[OutpostListener, List[MessageType]]

    def __init__(self):
        self.__socket = None
        self.__message_queue = asyncio.Queue(maxsize=2**18)
        self.__main_loop = asyncio.get_event_loop()
        self.__listeners = {}

    async def __establish_socket(self):
        """
        Attempts to establish a (secure) Websocket-Connection to the server.
        If the connection fails, this co-routine returns and will re-try after 10 seconds (see connect() method).
        If the connection is successful, a Hello-Message will be sent to the server,
        containing the hardware's unique ID.
        """
        try:
            self.__socket = await websockets.connect(self.__SERVER_ADDRESS)
        except ConnectionRefusedError:
            self.__socket = None
            return

    async def __start_message_queues(self):
        """
        Creates the send/receive async co-routines.
        Awaits both co-routines and blocks any other execution until
        any of the co-routine has completed. This should only be the case
        if the connection to the server is lost.
        """
        consumer = asyncio.ensure_future(self.__listen_for_messages())
        producer = asyncio.ensure_future(self.__send_messages())
        await asyncio.wait([consumer, producer])

    async def __listen_for_messages(self):
        """
        Awaits the Websocket for new messages from the server.
        If the connection fails for any reason, this co-routine posts a CONNECTION_FAILED
        signal in the queue, returns and the program will attempt to reconnect.
        If a new message is received, it will be processed in the
        ``onMessage``-handler.
        """
        while True:
            try:
                raw_msg = await self.__socket.recv()
            except ConnectionClosed:
                self.__main_loop.call_soon_threadsafe(self.__message_queue.put_nowait, 'CONNECTION_FAILED')
                return
            self.__on_message(raw_msg)

    async def __send_messages(self):
        """
        Awaits the message queue for new messages.
        If a new message has been posted to the queue, it will attempt
        to send it to the server as a serialized object.
        If the receiving co-routine has posted a CONNECTION_FAILED signal,
        the co-routine will return and allow the program to re-establish the connection
        before any further message processing is resumed.
        """

        await self.__socket.send(HelloMessage(hwid=self.__HWID).serialize())

        while True:
            msg: AbstractMessage = await self.__message_queue.get()
            if msg == 'CONNECTION_FAILED':
                return
            try:
                await self.__socket.send(msg.serialize())
            except ConnectionClosed:
                return
            self.__message_queue.task_done()

    def __on_message(self, raw: str):
        """
        Handler for new messages received from the server.
        It will attempt to decode the received string as JSON-object.

        :param raw: {str} Raw message received from the server.
        """

        msg_obj = None

        try:
            msg = json.loads(raw)
        except JSONDecodeError:
            return

        msg_type = MessageType(msg.get('msgType', 0))

        if msg_type == MessageType.SETTINGS:
            msg_obj = Settings.deserialize(raw)

        for listener, types in self.__listeners.items():
            if types is None or types and MessageType(msg.get('msgType', 0)) in types:
                listener.on_message(msg_obj if msg_obj is not None else msg)

    def connect(self):
        """
        Attempts to establish a connection to the server and run the message loop.
        Note: This method is blocking and should be invoked AFTER all other setup.
        If a connection cannot be established, this method will keep trying until successful,
        allowing 10 Seconds of hold-off time between attempts.
        """
        while True:
            asyncio.get_event_loop().run_until_complete(self.__establish_socket())
            if self.__socket:
                asyncio.get_event_loop().run_until_complete(self.__start_message_queues())

            # If any of the send/receive co-routines above aborts, this here point is reached
            # and we wait 10 seconds until we re-attempt to connect to the server.
            time.sleep(Outpost.__CONNECTION_FAIL_HOLDOFF_TIME)

    def register_listener(self, listener: OutpostListener, message_types: List[MessageType] = None):
        """
        Registers a new listener for incoming messages. If ``message_types`` are specified, only
        messages of types contained in that list will be forwarded to the listener.
        :param listener: {ifOutpostListener} Listener to be added.
        :param message_types: {List[MessageType]} Message type filter for this listener.
        """
        if listener not in self.__listeners:
            self.__listeners.setdefault(listener, message_types)

    # ============================ LogConsumer Methods =================================
    def consume_log_message(self, msg: AbstractMessage):
        """
        Called when new messages arrive via Websocket.
        :param msg:
        :return:
        """
        msg.hwid = self.__HWID
        self.__main_loop.call_soon_threadsafe(self.__message_queue.put_nowait, msg)
