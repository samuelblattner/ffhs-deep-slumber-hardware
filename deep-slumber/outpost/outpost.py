from typing import List

from outpost.exceptions import OutpostConnectionException
from outpost.interfaces import OutpostListener
from outpost.message import AbstractMessage, HelloMessage
import websockets
import asyncio




class Outpost:

    HWID = 1

    __socket = None
    listeners: List[OutpostListener]

    async def listen_for_messages(self):
        async with websockets.connect('ws://192.168.1.41:8777') as self.__socket:
            await self.__socket.send(HelloMessage(hwid=self.HWID).serialize())
            while True:
                raw_msg = await self.__socket.recv()
                self.onMessage(raw_msg)

    def connect(self) -> bool:
        asyncio.get_event_loop().run_until_complete(self.listen_for_messages())
        return True

    def disconnect(self):
        pass

    def getSettings(self):
        return

    def registerListener(self, listener: OutpostListener):
        if listener not in self.listeners:
            self.listeners.append(listener)

    def sendMessage(self, msg: AbstractMessage):
        pass

    def onMessage(self, raw: str):
        print('MESSSAGGGEEEEEE')
        print(raw)

