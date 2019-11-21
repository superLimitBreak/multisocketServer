from collections import defaultdict
import signal
import asyncio
import websockets
import umsgpack

import logging
log = logging.getLogger(__name__)


class SubscriptionServer():

    def __init__(self):
        #self.clients = set()
        self.subscriptions = defaultdict(set)

    async def subscription_server(self, websocket, path):
        self.subscriptions[websocket]
        log.info(f'connected: {websocket.remote_address}')
        try:
            async for message in websocket:
                for client, client_subscriptions in self.subscriptions.items():
                    await client.send(message)
        except Exception:
            log.exception('Its broken')
        finally:
            del self.subscriptions[websocket]
            log.info(f'disconnected: {websocket.remote_address}')

    def start(self):
        loop = asyncio.get_event_loop()
        stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
        async def server_with_stop(stop):
            async with websockets.serve(self.subscription_server, "localhost", 8765):
                await stop
        loop.run_until_complete(server_with_stop(stop))
        loop.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SubscriptionServer().start()
