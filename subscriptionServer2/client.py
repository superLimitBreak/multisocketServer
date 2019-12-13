import datetime
import asyncio
import socket
from multiprocessing.queues import Empty as MultiprocessingQueueEmpty
import aioprocessing


import websockets
import umsgpack

import logging


DEFAULT_RECONNECT_TIMEOUT = datetime.timedelta(seconds=5)


class SocketReconnect():
    """
    https://docs.python.org/3/library/asyncio.html
    https://realpython.com/async-io-python/
    https://github.com/dano/aioprocessing
    https://pymotw.com/3/asyncio/executors.html
    https://hackernoon.com/python-async-decorator-to-reduce-debug-woes-nv2dg30q5

    https://stackoverflow.com/questions/44853757/asynchronously-wait-for-multiprocessing-queue-in-main-process
    https://stackoverflow.com/questions/24687061/can-i-somehow-share-an-asynchronous-queue-with-a-subprocess
    https://docs.python.org/3/library/asyncio-dev.html#concurrency-and-multithreading
    https://hackernoon.com/threaded-asynchronous-magic-and-how-to-wield-it-bba9ed602c32
    https://quentin.pradet.me/blog/using-asynchronous-for-loops-in-python.html
    """
    def __init__(
        self,
        uri="ws://localhost:9873",
        timeout_reconnect=DEFAULT_RECONNECT_TIMEOUT,
        #buffer_failed_sends=False,
        loads=umsgpack.loads,
        dumps=umsgpack.dumps,
        name=__name__,
    ):
        self.name = name
        self.log = logging.getLogger(name)
        self.uri = uri
        self.timeout_reconnect = timeout_reconnect if isinstance(timeout_reconnect, datetime.timedelta) else datetime.timedelta(seconds=timeout_reconnect)
        self.timeout_msg = self.timeout_reconnect  # temp
        self.timeout_ping = self.timeout_reconnect  # temp
        #self.buffer_failed_sends = buffer_failed_sends
        self.loads = loads
        self.dumps = dumps
        self.queue_recv = aioprocessing.AioQueue()
        self.queue_send = aioprocessing.AioQueue()

        self.active = True
        self.websocket = None
        self.process = None

    def start_process(self):
        from multiprocessing import Process
        self.process = Process(target=self.start_asyncio, daemon=True)
        self.process.start()
    def start_asyncio(self):
        try:
            asyncio.run(self.asyncio_main())
        except KeyboardInterrupt:
            pass
    async def asyncio_main(self):
        await asyncio.gather(
            self._listen_forever(),
            self._monitor_send_queue(),
        )

    #@property
    #def connected(self):
    #    return self.active and self.websocket

    def close(self):
        self.active = False
        if self.process:
            self.process.terminate()

    async def _listen_forever(self):
        """
        Auto Reconnect Pattern - https://github.com/aaugustin/websockets/issues/414
        """
        while self.active:
            try:
                self.log.info(f'connecting: {self.uri}')
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
                        self.onMessage(self.loads(data))
                    self.onDisconnected()
            except asyncio.CancelledError:
                break
            except Exception as ex:
                self.log.exception('Websocket processing error')
                self.websocket = None
                #self.log.info('Its broken')
            #except socket.gaierror:
            #    self.log.info('Connection error?')
            #except ConnectionRefusedError:
            #    self.log.info('ConnectionRefusedError')
            if not self.websocket:
                await asyncio.sleep(self.timeout_reconnect.total_seconds())

    async def _monitor_send_queue(self):
        while self.active:
            #if not self.websocket:
            #    self.log.debug('No websocket. Wait 1')
            #    await asyncio.sleep(1)
            #    continue
            try:
                if not self.websocket:
                    await asyncio.sleep(0.1)
                    continue
                self.log.debug('_monitor_send_queue')
                message = await self.queue_send.coro_get(block=True, timeout=1)
                self.log.info(f'send: {message}')
                await self.websocket.send(self.dumps(message))
            except MultiprocessingQueueEmpty:
                pass
            except asyncio.CancelledError:
                break
            except Exception as ex:
                self.log.exception('Failed send')

    def send(self, data):
        self.queue_send.put_nowait(data)
    # To be overridden?
    def onMessage(self, data):
        self.queue_recv.put_nowait(data)
    def onConnected(self):
        self.log.info(f'onConnected {self.uri}')
    def onDisconnected(self):
        self.log.info(f'onDisconnected {self.uri}')


class SubscriptionClient(SocketReconnect):

    def __init__(self, *args, subscriptions=(), **kwargs):
        self.update_subscriptions(*subscriptions, send=False)
        super().__init__(*args, **kwargs)

    def update_subscriptions(self, *subscriptions, send=True):
        self.subscriptions = set(subscriptions) if subscriptions else set()
        if send:
            self.send_subscriptions()

    def send_subscriptions(self):
        self.send({
            'action': 'subscribe',
            'data': tuple(self.subscriptions),
        })

    def send_message(self, *messages):
        if not messages:
            return
        self.send({
            'action': 'message',
            'data': messages,
        })

    def onConnected(self):
        super().onConnected()
        self.send_subscriptions()

    def onMessage(self, data):
        if data and data.get('action') == 'message' and len(data.get('data', [])):
            for message in data.get('data'):
                super().onMessage(message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    socket = SubscriptionClient()
    socket.start_process()
    import pdb ; pdb.set_trace()
    pass
