import datetime
import asyncio
import socket

import websockets
import umsgpack

import logging
log = logging.getLogger(__name__)


# async def hello():
#     uri = "ws://localhost:8765"
#     async with websockets.connect(uri) as websocket:
#         data = {'hello': 'world'}
#         await websocket.send(umsgpack.dumps(data))
#         msg = umsgpack.loads(await websocket.recv())
#         print(msg)
# asyncio.get_event_loop().run_until_complete(hello())




DEFAULT_RECONNECT_TIMEOUT = datetime.timedelta(seconds=10)

class SocketReconnect(object):
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

    def start(self):
        asyncio.get_event_loop().run_until_complete(self._listen_forever())
    async def _listen_forever(self):
        """
        https://github.com/aaugustin/websockets/issues/414
        """
        while self.active:  # outer loop restarted every time the connection fails
            try:
                async with websockets.connect(self.uri) as ws:
                    self.websocket = ws
                    log.info(f'Connected {self.uri}')
                    self.onConnected()
                    while self.active:  # listener loop
                        try:
                            self._receive(
                                await asyncio.wait_for(self.websocket.recv(), timeout=self.timeout_msg.total_seconds())
                            )
                        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                            try:
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=self.timeout_ping.total_seconds())
                                log.debug('Ping OK, keeping connection alive...')
                                continue
                            except:
                                #await asyncio.sleep(self.timeout_reconnect.total_seconds())
                                break  # inner loop
                    self.onDisconnected()
            #except socket.gaierror:
            #    log.info('Connection error?')
            #except ConnectionRefusedError:
            #    log.info('ConnectionRefusedError')
            except Exception as ex:
                self.websocket = None
                log.info('Its broken')
            if not self.websocket:
                await asyncio.sleep(self.timeout_reconnect.total_seconds())

    def close(self):
        self.active = False

    def send(self, data):
        try:
            self.websocket.send(self._encode(data))
        except (socket.error, AttributeError):  # BrokenPipeError
            log.debug('Failed send. Socket not connected: {0}'.format(data))
            if self.buffer_failed_sends:
                log.error('Unimplemented add to buffer failed send')


    def _receive(self, data):
        self.receive(umsgpack.loads(data))

    # To be overridden
    def receive(self, data):
        log.info(data)

    def onConnected(self):
        log.info('onConnected')
    def onDisconnected(self):
        log.info('onDisconnected')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    SocketReconnect(uri="ws://localhost:8765")
