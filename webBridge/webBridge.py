import falcon
import json

from client_reconnect import SubscriptionClient

DEFAULT_PORT = 10794
DEFAULT_SUBSCRIPTIONSERVER_HOST = 'localhost:9872'


class URLtoSubscriptionServerBridge():
    def __init__(self, subscription_client):
        self.client = subscription_client

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

def create_wsgi_app(subscriptionserver_host=None, **kwargs):
    subscriptionserver_host = subscriptionserver_host or DEFAULT_SUBSCRIPTIONSERVER_HOST

    def parse_hostname_port(host):
        data = host.split(':')
        if len(data) == 1:
            return {'host': data[0]}
        if len(data) == 2:
            return {'host': data[0], 'port': int(data[1])}
        raise AttributeError(f'host {host} un-parseable')

    subscription_client = SubscriptionClient(**parse_hostname_port(subscriptionserver_host))

    app = falcon.API()
    app.add_route('/', URLtoSubscriptionServerBridge(subscription_client))
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
    parser.add_argument('--port', action='store', default=DEFAULT_PORT, type=int, help='')

    parser.add_argument('subscriptionserver_host', action='store', default=DEFAULT_SUBSCRIPTIONSERVER_HOST, help='')

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
    init_sigterm_handler()
    kwargs = get_args()

    from wsgiref import simple_server
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], create_wsgi_app(**kwargs))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
