import pytest

from ..server import SubscriptionServer, DEFAULT_PORT
from ..client import SubscriptionClient

import time
import socket
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Utils ------------------------------------------------------------------------

def is_port_open(port=DEFAULT_PORT, host='localhost'):
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((host, port)) == 0
def wait_for_port(port=DEFAULT_PORT):
    for attempt in range(10):
        if is_port_open():
            return
        time.sleep(0.1)
    raise Exception(f'Port: {port} did not open')

# Fixtures ---------------------------------------------------------------------

@pytest.fixture(scope='session')
def server():
    server = SubscriptionServer(auto_subscribe_to_all_fallback=True)
    server.start_process()
    wait_for_port()
    yield server
    server.close()

@pytest.fixture
def client(server):
    client = SubscriptionClient()
    client.start_process()
    yield client
    client.close()

@pytest.fixture
def client2(server):
    client = SubscriptionClient()
    client.start_process()
    yield client
    client.close()

# Tests ------------------------------------------------------------------------

def test_server(server, client, client2):
    message = {'a': 1, 'b': 2}
    client.send_message(message)
    assert client2.queue_recv.get(timeout=1) == message
