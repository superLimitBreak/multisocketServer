# Dear Python3 ... this is retarded ...
try:
    from .multisocket_server import ServerManager, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT
except (SystemError, ModuleNotFoundError):
    from multisocket_server import ServerManager, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT


import json
from collections import defaultdict

import logging
log = logging.getLogger(__name__)

__version__ = 0.01

_ATTR_PARTIAL_MESSAGE = '_partial_message'


class SubscriptionEchoServerManager(ServerManager):

    def __init__(self, *args, prevent_echo_back_to_source=False, auto_subscribe_to_all_fallback=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.prevent_echo_back_to_source = prevent_echo_back_to_source
        self.auto_subscribe_to_all_fallback = auto_subscribe_to_all_fallback
        self.subscriptions = defaultdict(set)
        self.actions = {
            'subscribe': self._action_subscribe,
            'message': self._action_message,
        }

    def connect(self, client):
        log.info('connection: %s connected' % client.id)
        self.subscriptions[client]

    def disconnect(self, client):
        log.info('connection: %s disconnected' % client.id)
        del self.subscriptions[client]

    def recv(self, data, source=None):
        log.debug('message: {0} - {1}'.format(getattr(source, 'id', None), str(data, 'utf8')))
        for line in filter(None, data.decode('utf-8').split('\n')):
            # TODO: This string looking for messages is FRAGILE and fraught with peril.
            #  This needs rethinking
            if not line.endswith('}'):  # the json package format always ends with the 'payload' object. This only works if the json is serialised in key order and the 'payload' is last. This is not guaranteed and fucking aweful.
                partial_messages = getattr(source, _ATTR_PARTIAL_MESSAGE, [])
                partial_messages.append(line)
                setattr(source, _ATTR_PARTIAL_MESSAGE, partial_messages)
                #log.debug(f'setting incomplete message - {line}')
                continue
            if not line.startswith('{'):
                partial_message = ''.join(getattr(source, _ATTR_PARTIAL_MESSAGE, []))
                setattr(source, _ATTR_PARTIAL_MESSAGE, [])
                #log.debug(f'reconstructing incomplete message - {partial_message} - {line}')
                line = partial_message + line
            try:
                message = json.loads(line)
            except json.decoder.JSONDecodeError:
                log.exception('Unable to json decode message: {0}'.format(line))
                continue
            try:
                assert isinstance(message, dict), 'Top level json object must be a dict'
            except Exception:
                log.exception('Message not dict?: {0}'.format(line))
                continue

            action = message.get('action')
            if action not in self.actions:
                log.warn('No action handler for {0}'.format(action))
                continue
            self.actions[action](message.get('data'), source)

    def stop(self):
        self.send(b'server_shutdown')
        super().stop()

    # --------------------------------------------------------------------------

    def _action_subscribe(self, data, source):
        """
        Update subscriptions for client
        """
        def parse_subscription_set(keys):
            if not keys:
                return set()
            if isinstance(keys, (str, bytes)):
                return {keys}
            return set(keys)
        self.subscriptions[source] = parse_subscription_set(data)
        return

    def _action_message(self, data, source):
        """
        Send message to subscribed clients
        """
        for client, client_subscriptions in self.subscriptions.items():
            if self.prevent_echo_back_to_source and client == source:
                continue
            messages_for_this_client = [
                m for m in data
                if (self.auto_subscribe_to_all_fallback and not client_subscriptions)
                or isinstance(m, dict) and m.get('deviceid') in client_subscriptions
            ]
            if not messages_for_this_client:
                continue
            client.send(
                json.dumps({
                    'action': 'message',
                    'data': messages_for_this_client
                }).encode('utf-8') + b'\n',
                source
            )


# Command line -----------------------------------------------------------------

def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog        = "SubscriptionMultiServe",
        description = "Lightweight JSON Subscription server for UDP, TCP and WebSockets",
        epilog      = "@calaldees"
    )
    parser.add_argument('--version', action='version', version="%.2f" % __version__)
    parser.add_argument('-t', '--tcp_port', type=int, help='TCP port', default=DEFAULT_TCP_PORT)
    parser.add_argument('-w', '--websocket_port', type=int, help='WebSocket port', default=DEFAULT_WEBSOCKET_PORT)
    parser.add_argument('--prevent_echo_back_to_source', action='store_true', help='Prevent messages sent from self being reflected back to self', default=False)
    parser.add_argument('--auto_subscribe_to_all_fallback', action='store_true', help='If no explicit subscriptions are given then subscribe to all messages', default=False)
    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.DEBUG)

    args = parser.parse_args()
    return vars(args)

def init_sigterm_handler():
    """
    Docker Terminate
    https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
    """
    import signal
    def handle_sigterm(*args):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    options = get_args()
    logging.basicConfig(level=options['log_level'])
    init_sigterm_handler()

    manager = SubscriptionEchoServerManager(**options)
    import time
    try:
        manager.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("")
    manager.stop()
    print("")
