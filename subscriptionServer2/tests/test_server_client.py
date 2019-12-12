import pytest

from ..server import SubscriptionServer
from ..client import SubscriptionClient

import time
import logging
logging.basicConfig(level=logging.INFO)

# Fixtures ---------------------------------------------------------------------

@pytest.fixture(scope='session')
def server():
    server = SubscriptionServer(auto_subscribe_to_all_fallback=True)
    server.start_process()
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
