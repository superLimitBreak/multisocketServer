import pytest

import time
import socket
import logging
from functools import partial
from multiprocessing.queues import Empty as QueueEmptyException

from ..server import SubscriptionServer, DEFAULT_PORT
from ..client import SubscriptionClient


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Utils ------------------------------------------------------------------------

def wait_for(_func, trys=10, sleep=0.1, message_fail='failed wait_for'):
    assert callable(_func)
    for attempt in range(trys):
        if _func():
            return
        time.sleep(sleep)
    raise Exception(message_fail)
def is_port_open(port=DEFAULT_PORT, host='localhost'):
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((host, port)) == 0

def wait_client_queue_recv_empty(*clients, timeout=1):
    _time_start = time.time()
    for client in clients:
        try:
            data = client.queue_recv.get(timeout=max(timeout-time.time()-_time_start, 0))
        except QueueEmptyException:
            continue
        raise Exception(f'Queue for {client.name} expected to be empty but got {data}')

# Fixtures ---------------------------------------------------------------------

@pytest.fixture(scope='session')
def server():
    server = SubscriptionServer(auto_subscribe_to_all_fallback=True)
    server.start_process()
    wait_for(is_port_open, message_fail=f'server port:{DEFAULT_PORT} did not open')
    yield server
    server.close()

@pytest.fixture
def client1(server):
    client = SubscriptionClient(name='client1')
    client.start_process()
    yield client
    client.close()

@pytest.fixture
def client2(server):
    client = SubscriptionClient(name='client2')
    client.start_process()
    yield client
    client.close()

@pytest.fixture
def client3(server):
    client = SubscriptionClient(name='client3')
    client.start_process()
    yield client
    client.close()

# Tests ------------------------------------------------------------------------

def test_server_client_basic_send(client1, client2):
    message = {'a': 1, 'b': 2}
    client1.send_message(message)
    assert client2.queue_recv.get(timeout=1) == message

def test_server_client_subscribe_send(client1, client2, client3):
    wait_for_all_clients_empty = partial(wait_client_queue_recv_empty, client1, client2, client3)
    client1.update_subscriptions('clients_all', 'clients_group_a', 'client1')
    client2.update_subscriptions('clients_all', 'clients_group_a', 'client2')
    client3.update_subscriptions('clients_all', 'clients_group_b', 'client3')
    time.sleep(0.1)

    message = {'deviceid': 'clients_all', 'a': 1}
    client1.send_message(message)
    assert client2.queue_recv.get(timeout=1) == message
    assert client3.queue_recv.get(timeout=1) == message
    wait_for_all_clients_empty()

    message = {'deviceid': 'clients_group_a', 'b': 2}
    client1.send_message(message)
    assert client2.queue_recv.get(timeout=1) == message
    wait_for_all_clients_empty()

    message = {'deviceid': 'clients_group_b', 'c': 1}
    client1.send_message(message)
    assert client3.queue_recv.get(timeout=1) == message
    wait_for_all_clients_empty()
