import logging
import json

import falcon

from subscriptionServer2.client import SubscriptionClient


DEFAULT_PORT = 10794
DEFAULT_SUBSCRIPTIONSERVER_URI = 'ws://localhost:9873'

log = logging.getLogger(__name__)


class URLtoSubscriptionServerBridge():
    def __init__(self, subscription_client):
        self.client = subscription_client

    def on_get(self, request, response):
        # Construct messages
        try:
            messages = json.load(request.bounded_stream)
        except json.decoder.JSONDecodeError:
            messages = {}
        if not isinstance(messages, (list, tuple)):
            messages = (messages, )
        deviceids = ','.join(request.path.strip('/').split('/'))
        if deviceids:
            request.params['deviceid'] = deviceids
        messages[0].update(request.params)
        log.info(messages)

        # Send messages
        if self.client.queue_send.empty():  # TODO: actually check if connected?
            self.client.send_message(*messages)
            response.status = falcon.HTTP_200
            response.media = {'status': 'ok'}
        else:
            response.status = falcon.HTTP_500
            response.media = {'status': 'socket connection issue'}

    #def on_post(self, request, response):
    #    # TODO: POST request
    #    response.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def create_wsgi_app(subscriptionserver_uri=None, **kwargs):
    subscription_client = SubscriptionClient(subscriptionserver_uri or DEFAULT_SUBSCRIPTIONSERVER_URI)
    subscription_client.start_process()

    handler = URLtoSubscriptionServerBridge(subscription_client)

    app = falcon.API()
    app.add_sink(handler.on_get, prefix='/')
    #app.add_route('/', URLtoSubscriptionServerBridge(subscription_client))
    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
            Provide a URL endpoint to send event triggers via a url to a running subscription_server.py

            curl -GET http://localhost:10794/front?func=text.html_bubble&html=test
            curl -XGET http://localhost/event/ -d '{"deviceid": "main", "func": "text.html_bubble", "html": "<h1>Test</h1><p>test</p>"}'
            curl -XGET http://localhost:9873/ -d '{"function": "screen_size.set", "deviceid": "main", "top":"100px", "left":"100px", "width": "400px", "height":"300px"}'


        ''',
    )

    parser.add_argument('subscriptionserver_uri', action='store', default=DEFAULT_SUBSCRIPTIONSERVER_URI, help='')

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=DEFAULT_PORT, type=int, help='')
    parser.add_argument('--log_level', type=int, help='log level', default=logging.INFO)

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
    logging.basicConfig(level=kwargs['log_level'])

    from wsgiref import simple_server
    log.info('falcon webserver {host}:{port}'.format(**kwargs))
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], create_wsgi_app(**kwargs))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
