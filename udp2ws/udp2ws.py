import asyncio

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

    def onConnected(self, source):
        log.info(f'onConnected: {source.remote_address}')

    def onDisconnected(self, source):
        log.info(f'onDisconnected: {source.remote_address}')

    async def new_connection(self, websocket, path):
        self.connections[websocket]
        self.onConnected(websocket)
        try:
            async for data in websocket:
                log.info(data)
        except websockets.ConnectionClosedError as ex:
            log.debug('ConnectionClosedError')
        except Exception as ex:
            log.exception('Error with websocket connection')
        finally:
            del self.connections[websocket]
            self.onDisconnected(websocket)

    async def serve_websocket(self):
        return websockets.serve(self.new_connection, "0.0.0.0", self.port_websocket)

    async def serve_udp(self):
        # https://docs.python.org/3/library/asyncio-protocol.html#asyncio-udp-echo-server-protocol
        log.info("Starting UDP server")
        return asyncio.get_running_loop().create_datagram_endpoint(
            self.EchoServerProtocol, 
            local_addr=('0.0.0.0', self.port_udp),
        )

    class EchoServerProtocol():
        def connection_made(self, transport):
            self.transport = transport

        def datagram_received(self, data, addr):
            message = data.decode()
            log.info('Received %r from %s' % (message, addr))
            log.info('Send %r to %s' % (message, addr))
            self.transport.sendto(data, addr)


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

    udp2ws = Udp2ws()
    asyncio.run(udp2ws.run(**kwargs))
