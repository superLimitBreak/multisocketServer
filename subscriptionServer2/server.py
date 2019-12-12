from collections import defaultdict
import signal
import operator
import asyncio

import websockets
import umsgpack

import logging
log = logging.getLogger(__name__)


__version__ = 0.01
DEFAULT_PORT = 9873


class SubscriptionServer():

    def __init__(self, port=DEFAULT_PORT, echo_back_to_source=False, auto_subscribe_to_all_fallback=False, **kwargs):
        self.port = port
        self.echo_back_to_source = echo_back_to_source
        self.auto_subscribe_to_all_fallback = auto_subscribe_to_all_fallback

        self.process = None
        self.stop = None

        self.actions = {
            'subscribe': self.actionSubscribe,
            'message': self.actionMessage,
        }
        self.subscriptions = defaultdict(set)

    def onConnected(self, source):
        log.info(f'onConnected: {source.remote_address}')

    def onDisconnected(self, source):
        log.info(f'onDisconnected: {source.remote_address}')

    async def onMessage(self, source, data):
        try:
            await self.actions[data.get('action')](source, data.get('data'))
        except Exception as ex:
            log.exception(f'Error processing message - source:{source.remote_address} data:{data}')

    @staticmethod
    def _parse_subscription_set(keys):
        if not keys:
            return set()
        if isinstance(keys, (str, bytes)):
            return {map(operator.attrgetter('strip'), keys.split(','))}
        return set(keys)
    async def actionSubscribe(self, source, data):
        self.subscriptions[source] = self._parse_subscription_set(data)
        log.info(f'subscribe: {source.remote_address} {self.subscriptions[source]}')

    async def actionMessage(self, source, data):
        for client, client_subscriptions in self.subscriptions.items():  # TODO: add async iter to end to multiple clients fast
            if not self.echo_back_to_source and client == source:
                continue
            messages_for_this_client = tuple(
                message for message in data
                if
                (self.auto_subscribe_to_all_fallback and not client_subscriptions)
                or
                (set(message.get('deviceid').split(',')) & client_subscriptions)  # (isinstance(message, dict) and
            )
            if not messages_for_this_client:
                continue
            log.info(f'message: {source.remote_address} {messages_for_this_client}')
            await client.send(umsgpack.dumps(
                {'action': 'message', 'data': messages_for_this_client}
            ))

    async def subscription_server(self, source, path):
        self.subscriptions[source]
        self.onConnected(source)
        try:
            async for data in source:
                await self.onMessage(source, umsgpack.loads(data))
        except websockets.ConnectionClosedError as ex:
            log.debug('ConnectionClosedError')
        except Exception as ex:
            log.exception('Error with websocket connection')
        finally:
            del self.subscriptions[source]
            self.onDisconnected(source)

    def close(self):
        log.info('close')
        if self.stop:
            self.stop.set_result()
        if self.process:
            self.process.terminate()
        log.info('close done')

    def start_asyncio(self):
        log.info(f'Starting: port:{self.port}')
        loop = asyncio.get_event_loop()
        self.stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, self.stop.set_result, None)
        async def server_with_stop(stop):
            async with websockets.serve(self.subscription_server, "0.0.0.0", self.port):
                await stop
        try:
            loop.run_until_complete(server_with_stop(self.stop))
        except KeyboardInterrupt as ex:
            pass
        finally:
            log.info('Shutdown')
    def start_process_daemon(self):
        from multiprocessing import Process
        self.process = Process(target=self.start_asyncio)
        self.process.start()


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog        = "SubscriptionServer2",
        description = "Lightweight msgpack Subscription server for WebSockets",
        epilog      = "@calaldees"
    )
    parser.add_argument('--version', action='version', version="%.2f" % __version__)
    parser.add_argument('-p', '--port', type=int, help='WebSocket port', default=DEFAULT_PORT)
    parser.add_argument('--echo_back_to_source', action='store_true', help='Reflect messages back to source', default=False)
    parser.add_argument('--auto_subscribe_to_all_fallback', action='store_true', help='If no explicit subscriptions are given then subscribe to all messages', default=False)
    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.INFO)

    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    options = get_args()
    logging.basicConfig(level=options['log_level'])

    SubscriptionServer(**options).start_asyncio()
