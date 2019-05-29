#!/usr/bin/env python

import re
import hashlib
import base64
import threading
import time
import socketserver
import socket
import struct
from multiprocessing import Process

import logging
logger = {
    'status'    : logging.getLogger(__name__+'.status').info,
    'connection': logging.getLogger(__name__+'.connection').info,
    'message': logging.getLogger(__name__+'.message').info,
}


# Constants---------------------------------------------------------------------
__version__ = 0.1
RECV_SIZE = 4096

DEFAULT_TCP_PORT = 9872
DEFAULT_WEBSOCKET_PORT = 9873

#options_defaults = {
#    'udp_port': 9871,
#    'tcp_port': 9872,
#    'websocket_port':9873,
#    'hide_status': True,
#    'hide_connections': True,
#    'show_messages':False,
#}


def log(catagory, msg):
    logger.get(catagory, lambda msg: None)(msg.strip())


class TCPBaseServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


# Binary Helpers ---------------------------------------------------------------

def ByteToHex(byteStr):
    """
    Convert a byte string to it's hex string representation e.g. for output.

    TODO Docstring
    """
    return ''.join(["%02X " % x for x in byteStr]).strip()  # ord( x )


def get_bit(number, bit):
    """
    The bit patern for the number 4 is '00000100'
    The third bit is True

    >>> get_bit(4,1)
    False
    >>> get_bit(4,2)
    False
    >>> get_bit(4,3)
    True
    >>> get_bit(4,4)
    False
    """
    return number & pow(2, bit-1) != 0

# Other ------------------------------------------------------------------------

    #ip = []
    ##import socket
    ##ip = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
    #try:
    #    # sudo apt-get install python-netifaces
    #    from netifaces import interfaces, ifaddresses, AF_INET
    #    for ifaceName in interfaces():
    #        ip += [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':''}] )]
    #        #print '%s: %s' % (ifaceName, ', '.join(addresses))
    #except:
    #    pass

# WebSocket --------------------------------------------------------------------

# HYBI10 ----

OPCODE_CONTINUATION =  0
OPCODE_TEXT         =  1
OPCODE_BINARY       =  2
OPCODE_CLOSE        =  8
OPCODE_PING         =  9
OPCODE_PONG         = 10

WEBSOCKET_HANDSHAKE_HYBI10 = """HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: %(websocket_accept)s\r\n\r\n"""


def websocket_frame_decode_hybi10(data):
    while data:
        payload_data, opcode, data = _websocket_frame_decode_hybi10(data)
        yield payload_data, opcode


def _websocket_frame_decode_hybi10(data):
    """
    http://tools.ietf.org/html/rfc6455#section-5.2
    """
    # Convert data to python 'int's to use bitwise operators
    #print(type(data[0]))
    #import pdb
    #pdb.set_trace()
    # Python2.x needs to convert data to ints. Python3.x has them as int's already
    if type(data[0]) != int:
        data = [ord(i) for i in data]

    # Extract control bits
    fin            = get_bit(data[0], 8)
    opcode         = data[0] % pow(2, 4)
    masked         = get_bit(data[1], 8)
    payload_length = data[1] % pow(2, 7)
    #print ("fin:%s opcode:%s masked:%s payload_length:%s" % (fin, opcode, masked, payload_length))

    if not fin:
        raise Exception('unsuported fragmented frames')

    # Payload Length - decode the length in bytes of the payload,
    # 126 and 127 are special values to decode the subsiquent bytes in another way
    data_start_point = 2
    extended_payload_length = 0
    if payload_length == 126:
        extended_payload_length = 2
        payload_length = struct.unpack('>H', data[data_start_point:data_start_point+extended_payload_length])[0]
    elif payload_length == 127:
        extended_payload_length = 8
        payload_length = struct.unpack('>L', data[data_start_point:data_start_point+extended_payload_length])[0]
    data_start_point += extended_payload_length

    # Mask
    masking_key = [0, 0, 0, 0]
    if masked:
        mask_length = len(masking_key)
        masking_key = data[data_start_point:data_start_point+mask_length]
        data_start_point += mask_length

    # Convert payload_data to python type
    data_convert_function = lambda i: i  # AllanC - close frames can have data in, int's cant be concatinated with b''.join ... humm
    if opcode == OPCODE_TEXT:
        pass
    #    data_convert_function = chr
    if opcode == OPCODE_BINARY:
        raise Exception('untested binary characters')
        pass

    payload_data = data[data_start_point:data_start_point+payload_length]
    assert len(payload_data) == payload_length, 'expected payload data size of {} but recived {}'.format(payload_length, len(payload_data))
    if masked:
        payload_data = bytes([data_convert_function(item ^ masking_key[index % 4]) for index, item in enumerate(payload_data)]) #b''.join(
    # AllanC - !? what about binary data? here we are just using a string. Wont that error on some values? advice?s

    return payload_data, opcode, data[data_start_point+payload_length:]


def websocket_frame_encode_hybi10(data, opcode=OPCODE_TEXT, fin=True, masked=False):
    if not fin:
        raise Exception('unsuported fragmented frames')

    # Create control byte
    control = int(fin) << 7 | opcode  # '\x81'

    # Create payload_length and extended_payload_length bytes
    payload_length = len(data)
    extended_payload_length = b''
    if payload_length > 65535:
        extended_payload_length = struct.pack('>L', payload_length)
        payload_length = 127
    elif payload_length > 125:
        extended_payload_length = struct.pack('>H', payload_length)
        payload_length = 126
    payload_length = int(masked) << 7 | payload_length

    # Create mask bytes
    if masked:
        raise Exception('unsuported masked')

    return bytes([control, payload_length]) + extended_payload_length + data

# HYBI00 ----

WEBSOCKET_HANDSHAKE_HYBI00 = """HTTP/1.1 101 Web Socket Protocol Handshake\r
Upgrade: WebSocket\r
Connection: Upgrade\r
WebSocket-Origin: %(origin)s\r
WebSocket-Location: %(location)s\r
WebSocket-Protocol: sample\r\n\r\n"""

#GET /demo HTTP/1.1
#Upgrade: WebSocket
#Connection: Upgrade
#Host: example.com
#Origin: http://example.com
#WebSocket-Protocol: sample

#HTTP/1.1 101 Web Socket Protocol Handshake
#Upgrade: WebSocket
#Connection: Upgrade
#WebSocket-Origin: http://example.com
#WebSocket-Location: ws://example.com/demo
#WebSocket-Protocol: sample


def websocket_frame_decode_hybi00(data):
    yield data, OPCODE_TEXT


def websocket_frame_encode_hybi00(data):
    return '\x00' + data + '\xff'



# http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76

WEBSOCKET_HANDSHAKE_HIXIE76 = """GET / HTTP/1.1\r
Upgrade: WebSocket\r
Connection: Upgrade\r
Host: %(location)\r
Origin: %(origin)\r
Sec-WebSocket-Key1:%(key1)\r
Sec-WebSocket-Key2:%(key1)\r\n\r\n"""


# Connection Handlers ----------------------------------------------------------

#if kwargs['udp_port']:
#    self._register_server('udp'      , socketserver.UDPServer(('', kwargs['udp_port']), UDPEchoRequestHandler))

class UDPEchoRequestHandler(socketserver.BaseRequestHandler):
    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = True

    def handle(self):
        # TODO - clients need to register with the UDP handler
        data = self.request[0].strip()
        socket = self.request[1]
        #log('message',"{} wrote:".format(self.client_address[0]))
        #log('message',data)
        client_send(data, self.client_address)
        socket.sendto(data.upper(), self.client_address)


class WebSocketRequestHandler(socketserver.BaseRequestHandler):
    """
    Abstract class, implement client wrapper create
    this is not idea as this class has to be used with the client wrappers
    Think about maybe applying customisable post setup, disconnect overlays to fire at end of methods
    """

    def setup(self):
        websocket_request = self.request.recv(RECV_SIZE)
        if not websocket_request:  # Sometimes this method is called with no request after a real setup?! WTF? Abort
            return

        if b'Sec-WebSocket-Key1' in websocket_request:
            raise Exception('This server does not support the HIXIE76 protocol. This rfc is obsolete. This protocol is used by PhantomJS<2 and Safari')

        websocket_request = str(websocket_request, 'utf8')

        # Store the headers that this connection was created with
        # so we can use them for later processing (eg looking at
        # the session cookie for authentication)
        try:
            # HTTP Headers happen to use the same MIME
            # format as defined in the email spec.
            import email
            request_line, headers_alone = websocket_request.split('\r\n', 1)
            msg = email.message_from_string(headers_alone)
            self.original_headers = dict(msg.items())
        except Exception:
            self.original_headers = {}

        # HyBi 10 handshake
        if 'Sec-WebSocket-Key' in websocket_request:
            websocket_key     = re.search(r'Sec-WebSocket-Key:\s?(.*)', websocket_request).group(1).strip()
            websocket_accept  = base64.b64encode(hashlib.sha1(websocket_key.encode('utf8')+b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
            handshake_return  = WEBSOCKET_HANDSHAKE_HYBI10 % {'websocket_accept':str(websocket_accept,'utf8')}
            self.frame_encode_func = websocket_frame_encode_hybi10
            self.frame_decode_func = websocket_frame_decode_hybi10

        # HyBi 07 ?

        # hixie-75?

        # HyBi 00 handshake
        elif False:
            header_match = re.search(r'GET (?P<location>.*?) HTTP.*Origin:\s?(?P<origin>.*?)\s', websocket_request, flags=re.MULTILINE)
            print(header_match.groupdict())
            handshake_return = (WEBSOCKET_HANDSHAKE_HYBI00 % {'origin': 'TEMP', 'location': 'TEMP'}).encode('utf8')
            self.frame_encode_func = websocket_frame_encode_hybi00
            self.frame_decode_func = websocket_frame_decode_hybi00

        self.request.send(handshake_return.encode('utf8'))
        #print(handshake_return)

        self.client_wrapper = self.construct_client_wrapper_function()  # automatically pass's self as it's a function, kind of annoying, because it isnt a method function

    def handle(self):
        while True:
            data_recv = self.request.recv(RECV_SIZE)
            if not data_recv:
                break
            for data, opcode in self.frame_decode_func(data_recv):
                if opcode == OPCODE_TEXT:
                    self.client_wrapper.recv(data)
                elif opcode == OPCODE_CLOSE:
                    self.request.send(self.frame_encode_func(data, opcode=OPCODE_CLOSE))
                    break
                elif opcode == OPCODE_PING:
                    self.request.send(self.frame_encode_func(data, opcode=OPCODE_PONG))
                else:
                    raise Exception('Unknown Websocket OPCODE')

    def finish(self):
        if self.client_wrapper:
            self.client_wrapper.disconnect()
            self.client_wrapper = None


class TCPRequestHandler(socketserver.BaseRequestHandler):

    def setup(self):
        self.client_wrapper = self.construct_client_wrapper_function()

    def handle(self):
        while True:
            data = self.request.recv(RECV_SIZE)
            if not data:
                break
            self.client_wrapper.recv(data)

    def finish(self):
        self.client_wrapper.disconnect()


# Framework --------------------------------------------------------------------

class ClientWrapper():
    """
    An abstract client class to standardise how clients interact
    """
    id = ''

    def __init__(self, server_wrapper, client_obj):
        """
        Instansiated upon a real client connection
        ServerWrapper.connect(self) called to pass up handling of additional connection management
        """
        self.server = server_wrapper
        self.client_obj = client_obj
        self.connect()
        self.server.connect(self)

    def disconnect(self):
        self.server.disconnect(self)

    def recv(self, data):
        """
        Pass's message up to server_wrapper
        """
        self.server.recv(data,self)

    # Abstract Methods ------
    def send(self, data, source=None):
        """
        Required
        Optional source object, could be another client, could be a server, could be none
        """
        pass

    def close(self):
        """
        Required - close this connection
        """
        pass

    def connect(self):
        """
        Optonal - override for connected additional behaviour
        """
        pass


class ServerWrapper():

    def __init__(self, name, manager, **options):
        self.clients     = []
        self.server_obj  = None  # Set later at start_server_thread
        self.name        = name
        self.options     = options
        self.manager     = manager
        self.manager.servers[self.name] = self  # Register this server with manager

    def connect(self, client):
        """
        Child client has established a connection
        """
        #log('connection','add the client %s : %s' % (self.name, client.id)) # unneeded as echo server implmenting class handles logging
        self.clients.append(client)
        self.manager.connect(client)

    def disconnect(self, client):
        """
        Child client connection has dropped
        """
        self.manager.disconnect(client)
        self.clients.remove(client)

    def send(self, data, source=None):
        """
        Send data to all connected clients
        """
        for client in self.clients:
            client.send(data,source)

    def recv(self, data, source=None):
        """
        Data receved from child client
        default pass data up to manager
        """
        self.manager.recv(data, source)

    def start_server_thread(self):
        self.server_obj = self.get_server_obj()
        if self.server_obj:
            self.server_thread = threading.Thread(target=self.server_obj.serve_forever)
            #self.server_thread = Process(target=self.server_obj.serve_forever)
            self.server_thread.daemon = True   # Exit the server thread when the main thread terminates
            self.server_thread.start()         # Start a thread with the server -- that thread will then start one more thread for each request
        #print("Server loop running in thread:", server_thread.name)
            #import pdb ; pdb.set_trace()
            log('status','{0} Server on {1}'.format(self.name, self.server_obj.server_address))

    def close(self):
        """
        Close all client connections
        and close server
        The server will wait for all client connections to terminate and then exit the serve forever loop
        """
        for client in self.clients:
            client.close()
        self.close_server_obj()
        #self.server_thread.terminate()
        #self.server_thread.join()

    # Abstract methods ---------------

    def get_server_obj(self):
        """
        Required
        A server_obj should implement serve_forever to be used in a thread
        """
        pass

    def close_server_obj(self):
        """
        Required
        """
        pass


class ServerManager():

    def __init__(self, auto_setup_default_server_wrappers=True, **options):
        self.servers = {}
        if auto_setup_default_server_wrappers:
            if options.get('websocket_port'):
                WebsocketServerWrapper(self, **options)
            if options.get('tcp_port'):
                TCPServerWrapper      (self, **options)
            if options.get('udb_port'):
                UDPServerWrapper      (self, **options)

    def start(self):
        for server in self.servers.values():
            server.start_server_thread()
        log('status','ServerManager: running')

    def stop(self):
        log('status', 'ServerManager: shutting down')
        for server in self.servers.values():
            server.close()

    # Optional Override -----------------

    def connect(self, client):
        pass

    def disconnect(self, client):
        pass

    def send(self, data, source=None):
        """
        Send data to all subservers
        """
        for server in self.servers.values():
            server.send(data, source)

    # Required override ------------------

    def recv(self, data):
        """
        to be overridden
        """
        pass


# Server Implementations -------------------------------------------------------

class TCPServerWrapper(ServerWrapper):

    def __init__(self, manager, **options):
        super().__init__('tcp', manager, **options)

    # Client Class ---------------

    class TCPClientWrapper(ClientWrapper):
        def __init__(self, server_wrapper, client_obj):
            self.id = str(client_obj.client_address)
            super().__init__(server_wrapper, client_obj)
        def send(self, data, source=None):
            self.client_obj.request.sendall(data)
        def close(self):
            self.client_obj.request.shutdown(socket.SHUT_RDWR)

    # Server Implementation ----

    def get_server_obj(self):
        if self.server_obj:
            raise Exception("Server already running")
        class Handler(TCPRequestHandler):
            construct_client_wrapper_function = lambda client_obj: self.TCPClientWrapper(self, client_obj)
        return TCPBaseServer(('', self.options['tcp_port']), Handler)

    def close_server_obj(self):
        self.server_obj.shutdown()
        self.server_obj.server_close()
        self.server_thread.join()
        #self.server_obj.socket.shutdown(socket.SHUT_RDWR)  # It wont shut down properly!
        #assert False
        #Try ? http://stackoverflow.com/questions/5875177/how-to-close-a-socket-left-open-by-a-killed-program/5875178#5875178
        self.server_obj = None


class WebsocketServerWrapper(ServerWrapper):

    def __init__(self, manager, **options):
        super().__init__('websocket', manager, **options)

    # Client Class ---------------

    class WebsocetClientWrapper(ClientWrapper):
        def __init__(self, server_wrapper, client_obj):
            self.id = str(client_obj.client_address)
            super().__init__(server_wrapper, client_obj)
        def send(self, data, source=None):
            self.client_obj.request.sendall(self.client_obj.frame_encode_func(data))
        def close(self):
            self.client_obj.request.sendall(self.client_obj.frame_encode_func(b'', opcode=OPCODE_CLOSE))  # ?? Close frame? not needed in all version of websockets
            self.client_obj.request.shutdown(socket.SHUT_RDWR)

    # Server Implementation ----

    def get_server_obj(self):
        if self.server_obj:
            raise Exception("Server already running")
        class Handler(WebSocketRequestHandler):
            construct_client_wrapper_function = lambda client_obj: self.WebsocetClientWrapper(self, client_obj)
        return TCPBaseServer(('', self.options['websocket_port']), Handler)

    def close_server_obj(self):
        self.server_obj.shutdown()
        self.server_obj.server_close()
        self.server_obj = None


class UDPServerWrapper(ServerWrapper):

    def __init__(self, manager, **options):
        super().__init__('udp', manager, **options)

    def get_server_obj(self):
        return  # UDPServer(('', self.options['udp_port']), Handler)

    def close_server_obj(self):
        pass


# Manager Implementations ------------------------------------------------------

class EchoServerManager(ServerManager):
    def connect(self, client):
        log('connection', '%s connected' % client.id)  # TODO - add logging of what type of client it was

    def disconnect(self, client):
        log('connection', '%s disconnected' % client.id)

    def recv(self, data, source=None):
        log('message', '{0} - {1}'.format(getattr(source, 'id', None), str(data, 'utf8')))
        #if isinstance(data,str):
        #    data = data.encode('utf8')
        self.send(data, source)

    def stop(self):
        self.send(b'server_shutdown')
        super().stop()


# Command Line Arguments -------------------------------------------------------

def bool_(value):
    value = value.lower()
    for t in ['yes', 'true', 'y']:
        if t in value:
            return True
    return False


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog        = "EchoMultiServe",
        description = "Lightweight Echo server for UDP, TCP and WebSockets",
        epilog      = "@calaldees"
    )
    parser.add_argument('--version', action='version', version="%.2f" % __version__)
    #parser.add_argument('-s','--serve', nargs='+', choices=['udp', 'tcp', 'websocket'], metavar='SERVER_TYPE', default=['udp','tcp','websocket'])
    parser.add_argument('-u', '--udp_port'      , type=int, help='UDP port'      , default=9871)
    parser.add_argument('-t', '--tcp_port'      , type=int, help='TCP port'      , default=DEFAULT_TCP_PORT)
    parser.add_argument('-w', '--websocket_port', type=int, help='WebSocket port', default=DEFAULT_WEBSOCKET_PORT)
    parser.add_argument('-s', '--hide_status'     , action='store_true', default=False, help='Display status')
    parser.add_argument('-c', '--hide_connections', action='store_true', default=False, help='Display connections')
    parser.add_argument('-m', '--show_messages'   , action='store_true', default=False, help='Display messages recived')
    return parser.parse_args()

# Main -------------------------------------------------------------------------

if __name__ == "__main__":
    args = get_args()

    logging.basicConfig(level=logging.DEBUG)

    if args.hide_status:
        del logger['status']
    if args.hide_connections:
        del logger['connection']
    if not args.show_messages:
        del logger['message']

    options = vars(args)
    manager = EchoServerManager(**options)
    try:
        manager.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("")
    manager.stop()
    print("")
