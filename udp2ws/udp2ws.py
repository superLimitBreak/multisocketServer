import asyncio
import signal

import websockets

import logging
log = logging.getLogger(__name__)


class Udp2ws():
    
    def __init__(self, port_udp=None, port_websocket=None, **kwargs):
        assert port_websocket
        assert port_udp
        self.port_udp = port_udp
        self.port_websocket = port_websocket

        self.connections = set()
        self._queue_udp_messages = asyncio.Queue()
        log.info("there can be only one")

    async def _send_to_all_websockets(self):
        # https://stackoverflow.com/questions/53733140/how-to-use-udp-with-asyncio-for-multiple-file-transfer-from-server-to-client-p
        log.info("Starting udp queue listener")
        while True:
            log.info(f"waiting for the god damn queue {id(self._queue_udp_messages)}")
            data, addr = await self._queue_udp_messages.get()  # block=True, timeout=1
            log.info("2")
            for websocket in self.connections:
                await websocket.send(data)

    async def new_websocket_connection(self, websocket, path):
        self.connections.add(websocket)
        try:
            async for data in websocket:
                log.info(data)
        except websockets.ConnectionClosedError as ex:
            log.debug('ConnectionClosedError')
        except Exception as ex:
            log.exception('Error with websocket connection')
        finally:
            self.connections.remove(websocket)

    async def serve_websocket(self):
        log.info("Starting Websocket server")
        loop = asyncio.get_event_loop()
        self.stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, self.stop.set_result, None)
        async def server_with_stop(stop):
            async with websockets.serve(self.new_websocket_connection, "0.0.0.0", self.port_websocket):
                await stop
        await server_with_stop(self.stop)
        #try:
        #    loop.run_until_complete(server_with_stop(self.stop))
        #except KeyboardInterrupt as ex:
        #    pass
        #finally:
        #    log.info('Shutdown')

    async def serve_udp(self):
        class UdpReceiver(asyncio.DatagramProtocol):
            def __init__(self, queue):
                self.queue = queue
            def connection_made(self, transport):
                self.transport = transport
            def datagram_received(self, data, addr):
                log.info(f'{self.queue.qsize()} {data} {id(self.queue)}')
                self.queue.put_nowait((data, addr))

        log.info("Starting UDP server")
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(
            lambda: UdpReceiver(self._queue_udp_messages),
            local_addr=('0.0.0.0', self.port_udp),
        )

            #try:
            #except asyncio.QueueFull:
            #    log.warn('udp queue is full')
            
            #message = data.decode()
            #log.info('Received %r from %s' % (message, addr))
            #log.info('Send %r to %s' % (message, addr))
            #self.transport.sendto(data, addr)

    async def run(self):
        task1 = asyncio.create_task(self.serve_udp())
        task2 = asyncio.create_task(self.serve_websocket())
        task3 = asyncio.create_task(self._send_to_all_websockets())
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

    udp2ws = Udp2ws(**kwargs)
    asyncio.run(udp2ws.run())
    #udp2ws.serve_websocket()

    # echo "This is my data" > /dev/udp/127.0.0.1/12462