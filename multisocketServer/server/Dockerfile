FROM python:alpine

COPY \
    __init__.py \
    multisocket_server.py \
    subscription_server.py \
/multisocket/

ENTRYPOINT ["python3", "/multisocket/subscription_server.py"]
#CMD ["--help"]

ENV TCP_PORT=9872
ENV WEBSOCKET_PORT=9873

#EXPOSE TCP_PORT
#EXPOSE WEBSOCKET_PORT

# Cant use ENV variables in CMD. Maybe we could use ARGS?
CMD ["--tcp_port", "9872", "--websocket_port", "9873", "--log_level", "20"]

# TODO: Hea;thcheck cuold actually use Python client to route ping-pong messages?
HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
    CMD netstat -an | grep ${WEBSOCKET_PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# docker build -t superlimitbreak/subscriptionserver:latest --file subscription_server.dockerfile .
# docker run --rm -it -p 9872:9872 -p 9873:9873 superlimitbreak/subscriptionserver:latest


# TODO: Add multistage build test
