import socket
import datetime
import time
import json
#from multiprocessing import Process, Queue
import threading

import logging
log = logging.getLogger(__name__)

# Constants --------------------------------------------------------------------

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 9872
DEFAULT_RECONNECT_TIMEOUT = datetime.timedelta(seconds=5)


def timedelta_total_seconds(timedelta):
    """
    Hack polyfill for python3.1 missing total_seconds
    """
    if hasattr(timedelta, 'total_seconds'):
        return timedelta.total_seconds()
    else:
        # http://stackoverflow.com/questions/28089558/alternative-to-total-seconds-in-python-2-6
        return (
            timedelta.microseconds + 0.0 +
            (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6


# Null Handler -----------------------------------------------------------------

class SocketReconnectNull(object):

    def send(self, *args, **kwargs):
        log.debug(args)
        pass

    def close(self):
        pass


# Network Display --------------------------------------------------------------

class SocketReconnect(object):
    READ_SIZE = 4098

    #@staticmethod
    #def factory(*args, **kwargs):
    #    try:
    #        return SocketReconnect(*args, **kwargs)
    #    except socket.error:
    #        log.warn('Unable to setup TCP network socket {0} {1}'.format(args, kwargs))
    #        return SocketReconnectNull()

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, reconnect_timeout=DEFAULT_RECONNECT_TIMEOUT, autostart=True, buffer_failed_sends=False):
        self.host = host
        self.port = int(port)
        self.reconnect_timout = reconnect_timeout if isinstance(reconnect_timeout, datetime.timedelta) else datetime.timedelta(seconds=reconnect_timeout)
        self.buffer_failed_sends = buffer_failed_sends
        #self.socket_connected_attempted_timestamp = None
        self.active = True
        self.socket = None

        self.connection_thread = threading.Thread(target=self._recive)  #Process(  Attempted Python3 Process, but this wont share the obj reference to self.socket. There must be a better way of doing this than the old python2 threading module
        self.connection_thread.daemon = True
        if autostart:
            self.start()

    def start(self):
        self.connection_thread.start()

    def close(self):
        self.active = False
        try:
            self.socket.close()
        except Exception:
            pass

    def send(self, data):
        try:
            self.socket.sendall(self._encode(data))
        except (socket.error, AttributeError):  # BrokenPipeError
            log.debug('Failed send. Socket not connected: {0}'.format(data))
            if self.buffer_failed_sends:
                log.error('Unimplemented add to buffer failed send')

    def _recive(self):
        while self.active:
            log.debug('Attempting socket connection {0}:{1}'.format(self.host, self.port))
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
            except Exception:  # Todo: catch specific error?
                # "ConnectionRefusedError" in err.reason
                self.socket = None

            if self.socket:
                log.info('Connected {0}:{1}'.format(self.host, self.port))
                self._connected()
                if self.buffer_failed_sends:  # and failed_sends
                    log.error('Unimplemented send all the buffed buffer_failed_sends')

            try:
                while self.socket and self.active:  # self.socket.isConnected
                    data = self.socket.recv(self.READ_SIZE)
                    if not data:
                        break
                    for d in self._decode(data):
                        self.recive(d)
            except OSError:
                pass
            except KeyboardInterrupt:
                self.active = False
            except Exception as ex:  # OSError:
                log.exception(ex)

            if self.socket:
                if self.active:
                    log.info('Disconnected {0}:{1}. Retrying in background.'.format(self.host, self.port))
                self._disconnected()

            try:
                self.socket.close()
                self.socket.shutdown(socket.SHUT_RDWR)  # Is this needed?
            except Exception:  # Todo: catch specific error
                pass
            self.socket = None

            if self.active:
                time.sleep(timedelta_total_seconds(self.reconnect_timout))

    # Overrideable methods ---------

    def _encode(self, data):
        return data

    def _decode(self, data):
        yield data

    def _connected(self):
        log.debug('Connected')

    def _disconnected(self):
        log.debug('Diconnected')

    def recive(self, data):
        pass


class JsonSocketReconnect(SocketReconnect):
    #@staticmethod
    #def factory(*args, **kwargs):
    #    try:
    #        return JsonSocketReconnect(*args, **kwargs)
    #    except socket.error:
    #        log.warn('Unable to setup TCP network socket {0} {1}'.format(args, kwargs))
    #        return SocketReconnectNull()

    def _encode(self, data):
        return (json.dumps(data)+'\n').encode('utf-8')

    def _decode(self, data):
        for line in filter(None, data.decode('utf-8').split('\n')):
            try:
                yield json.loads(line)
            except json.decoder.JSONDecodeError:
                log.warn('Unable to decode json %s', line)
                continue


class SubscriptionClient(JsonSocketReconnect):
    """
    An implementation of the subscription server protocol
    To subscribe, subclass's are advised to manipulate the .subscribtions set directly
    """
    #@staticmethod
    #def factory(*args, **kwargs):
    #    try:
    #        return SubscriptionClient(*args, **kwargs)
    #    except Exception:
    #        import pdb ; pdb.set_trace()
    #        pass
    #    except socket.error:
    #        log.warn('Unable to setup TCP network socket {0} {1}'.format(args, kwargs))
    #        return SocketReconnectNull()

    def __init__(self, *args, subscriptions=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.update_subscriptions(*subscriptions, send=False)

    def update_subscriptions(self, *subscriptions, send=True):
        self.subscriptions = set(subscriptions) if subscriptions else set()
        if send:
            self.send_subscriptions()

    def send_message(self, *messages):
        if not messages:
            return
        self.send({
            'action': 'message',
            'data': messages,
        })

    def send_subscriptions(self):
        self.send({
            'action': 'subscribe',
            'data': tuple(self.subscriptions),
        })

    def _connected(self):
        self.send_subscriptions()

    def recive(self, data):
        if data and data.get('action') == 'message' and len(data.get('data', [])):
            for message in data.get('data'):
                self.receive_message(message)

    # To be overridden
    def receive_message(self, message):
        pass


class ExampleSocketReconnect(SocketReconnect):
    def recive(self, data):
        print(data)


# Main Demo --------------------------------------------------------------------

if __name__ == "__main__":

    try:
        client = ExampleSocketReconnect()
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("")
