import datetime
import asyncio
import socket
from multiprocessing import Queue


import websockets
import umsgpack

import logging
log = logging.getLogger(__name__)


DEFAULT_RECONNECT_TIMEOUT = datetime.timedelta(seconds=10)


class SocketReconnect(object):
    """
    https://docs.python.org/3/library/asyncio-task.html
    https://realpython.com/async-io-python/
    https://pymotw.com/3/asyncio/executors.html
    https://hackernoon.com/python-async-decorator-to-reduce-debug-woes-nv2dg30q5

    https://stackoverflow.com/questions/44853757/asynchronously-wait-for-multiprocessing-queue-in-main-process
    https://stackoverflow.com/questions/24687061/can-i-somehow-share-an-asynchronous-queue-with-a-subprocess
    https://docs.python.org/3/library/asyncio-dev.html#concurrency-and-multithreading
    https://hackernoon.com/threaded-asynchronous-magic-and-how-to-wield-it-bba9ed602c32
    https://quentin.pradet.me/blog/using-asynchronous-for-loops-in-python.html
    """
    def __init__(self, uri, timeout_reconnect=DEFAULT_RECONNECT_TIMEOUT, autostart=True, buffer_failed_sends=False):
        self.uri = uri
        self.timeout_reconnect = timeout_reconnect if isinstance(timeout_reconnect, datetime.timedelta) else datetime.timedelta(seconds=timeout_reconnect)
        self.timeout_msg = self.timeout_reconnect  # temp
        self.timeout_ping = self.timeout_reconnect  # temp
        self.buffer_failed_sends = buffer_failed_sends
        self.active = True
        self.websocket = None
        if autostart:
            self.start()
        self.queue_recv = Queue()
        self.queue_send = Queue()

    def start(self):
        asyncio.get_event_loop().run_until_complete(self._listen_forever())
    async def _listen_forever(self):
        """
        https://github.com/aaugustin/websockets/issues/414
        """
        while self.active:
            try:
                log.info('attempting')
                async with websockets.connect(self.uri) as self.websocket:
                    self.onConnected()
                    while self.active:
                        try:
                            data = await asyncio.wait_for(self.websocket.recv(), timeout=self.timeout_msg.total_seconds())
                        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                            try:
                                pong = await self.websocket.ping()
                                await asyncio.wait_for(pong, timeout=self.timeout_ping.total_seconds())
                                continue
                            except:
                                break
                        self._onMessage(data)
                    self.onDisconnected()
            except Exception as ex:
                self.websocket = None
                #log.info('Its broken')
            #except socket.gaierror:
            #    log.info('Connection error?')
            #except ConnectionRefusedError:
            #    log.info('ConnectionRefusedError')
            if not self.websocket:
                await asyncio.sleep(self.timeout_reconnect.total_seconds())

    def close(self):
        self.active = False

    async def send(self, data):
        try:
            await self.websocket.send(umsgpack.dumps(data))
        except Exception:
            log.debug('Failed send. Socket not connected: {0}'.format(data))

    def _onMessage(self, data):
        self.onMessage(umsgpack.loads(data))

    # To be overridden
    def onConnected(self):
        log.info(f'onConnected {self.uri}')
    def onDisconnected(self):
        log.info(f'onDisconnected {self.uri}')
    def onMessage(self, data):
        log.info(data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SocketReconnect(uri="ws://localhost:9873")
