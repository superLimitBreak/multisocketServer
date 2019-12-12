from ..server import SubscriptionServer
from ..client import SubscriptionClient

import time
#import logging

def test_server():
    #logging.basicConfig(level=logging.INFO)
    server = SubscriptionServer()
    server.start_process_daemon()
    time.sleep(1)
    server.close()
