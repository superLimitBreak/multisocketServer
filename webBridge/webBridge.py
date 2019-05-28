import falcon
import json

from client_reconnect import SubscriptionClient


DEFAULT_SUBSCRIPTION_SERVER_HOSTNAME = 'localhost:9872'


class URLtoSubscriptionServerBridge():
    def __init__(self, *args, **kwargs):
        self.client = SubscriptionClient(*args, **kwargs)

    def on_get(self, request, response):
        if self.client.socket:
            self.client.send_message({**json.load(request.stream), **request.params})
            response.status = falcon.HTTP_200
        else:
            response.status = falcon.HTTP_500

    #def on_post(self, request, response):
    #    # TODO: POST request
    #    response.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def create_wsgi_app(subscription_server_hostname=None, **kwargs):
    subscription_server_hostname = subscription_server_hostname or DEFAULT_SUBSCRIPTION_SERVER_HOSTNAME

    def parse_hostname_port(hostname):
        data = subscription_server_hostname.split(':')
        if len(data) == 1:
            return {'host': data[0]}
        if len(data) == 2:
            return {'host': data[0], 'port': int(data[1])}
        raise AttributeError(f'hostname {hostname} unparseable')

    app = falcon.API()
    app.add_route('/', URLtoSubscriptionServerBridge(**parse_hostname_port(subscription_server_hostname)))
    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
            Provide a URL endpoint to send event triggers via a url to a running subscription_server.py

            curl -XGET http://localhost:8000/ -d '{"function": "screen_size.set", "deviceid": "main", "top":"100px", "left":"100px", "width": "400px", "height":"300px"}'
        ''',
    )

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=8000, type=int, help='')

    parser.add_argument('--subscription_server_hostname', action='store', default=DEFAULT_SUBSCRIPTION_SERVER_HOSTNAME, help='')

    kwargs = vars(parser.parse_args())
    return kwargs


def init_sigterm_handler():
    """
    Docker Terminate
    https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
    """
    import signal
    def handle_sigterm(*args):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, handle_sigterm)



# Main ------------------------------------------------------------------------

if __name__ == '__main__':
    kwargs = get_args()
    init_sigterm_handler()

    from wsgiref import simple_server
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], create_wsgi_app(**kwargs))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
