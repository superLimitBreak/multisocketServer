import asyncio
import signal

import websockets

import logging
log = logging.getLogger(__name__)


class Udp2ws():
    """
    Kind of a mess ... asyncio python is lame
    the udp transport receives messages not inside the async loop, so we have to add udp messages to a queue to be awaited in the loop. 
    I would have tidied up this file .. but I cant be arsed.
    asyncio python has just annoyed me and I dont want to work with it any more than I have to.
    I want to see if Golang is less lines of code than this farce
    """
    
    def __init__(self, port_udp=None, port_websocket=None, **kwargs):
        assert port_websocket
        assert port_udp
        self.port_udp = port_udp
        self.port_websocket = port_websocket

        self.connections = set()
        self.queue = None  # can only be inited inside loop 

    async def new_websocket_connection(self, websocket, path):
        self.connections.add(websocket)
        try:
            async for data in websocket:
                #log.info(data)
                pass  # ignore all received messages from websockets
        except websockets.ConnectionClosedError as ex:
            log.debug('ConnectionClosedError')
        except Exception as ex:
            log.exception('Error with websocket connection')
        finally:
            self.connections.remove(websocket)

    async def serve_websocket(self):
        log.info("Starting Websocket server")
        loop = asyncio.get_running_loop()
        self.stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, self.stop.set_result, None)
        async def server_with_stop(stop):
            async with websockets.serve(self.new_websocket_connection, "0.0.0.0", self.port_websocket):
                await stop
        await server_with_stop(self.stop)

    async def serve_udp(self):
        class UdpReceiver(asyncio.DatagramProtocol):
            def __init__(self, queue):
                self.queue = queue
            def connection_made(self, transport):
                self.transport = transport
            def datagram_received(self, data, addr):
                self.queue.put_nowait((data, addr))

        log.info("Starting UDP server")
        assert self.queue
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UdpReceiver(self.queue),
            local_addr=('0.0.0.0', self.port_udp),
        )

    async def listen_to_udp_queue(self):
        assert self.queue
        # https://stackoverflow.com/questions/53733140/how-to-use-udp-with-asyncio-for-multiple-file-transfer-from-server-to-client-p
        log.info("Starting udp queue listener")
        while True:
            data, addr = await self.queue.get()  # block=True, timeout=1
            for websocket in self.connections:
                await websocket.send(data)

    async def asyncio_entrypoint(self):
        self.queue = asyncio.Queue()  # https://stackoverflow.com/a/53724990/3356840
        task1 = asyncio.create_task(self.serve_udp())
        task2 = asyncio.create_task(self.serve_websocket())
        task3 = asyncio.create_task(self.listen_to_udp_queue())
        await task1
        await task2
        await task3


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog        = __name__,
        description = "",
        epilog      = "@calaldees"
    )
    parser.add_argument('-udp', '--port_udp', type=int, help='WebSocket port', default=12462)
    parser.add_argument('-ws', '--port_websocket', type=int, help='WebSocket port', default=9874)

    parser.add_argument('--log_level', action='store', type=int, help='loglevel of output to stdout', default=logging.INFO)

    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    kwargs = get_args()
    logging.basicConfig(level=kwargs['log_level'])

    asyncio.run(Udp2ws(**kwargs).asyncio_entrypoint())

    # echo "This is my data" > /dev/udp/127.0.0.1/12462