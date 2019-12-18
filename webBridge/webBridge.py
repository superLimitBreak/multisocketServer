import falcon
import json

from subscriptionServer2.client import SubscriptionClient

DEFAULT_PORT = 10794
DEFAULT_SUBSCRIPTIONSERVER_URI = 'ws://localhost:9873'


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

def create_wsgi_app(subscriptionserver_uri=None, **kwargs):
    subscription_client = SubscriptionClient(subscriptionserver_uri or DEFAULT_SUBSCRIPTIONSERVER_URI)

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

            curl -XGET http://localhost:9873/ -d '{"function": "screen_size.set", "deviceid": "main", "top":"100px", "left":"100px", "width": "400px", "height":"300px"}'
        ''',
    )

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=DEFAULT_PORT, type=int, help='')

    parser.add_argument('subscriptionserver_uri', action='store', default=DEFAULT_SUBSCRIPTIONSERVER_URI, help='')

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
