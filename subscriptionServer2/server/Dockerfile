FROM python:alpine

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY \
    subscription_server.py \
/subscriptionServer2/

ENTRYPOINT ["python3", "/subscriptionServer2/subscription_server.py"]
#CMD ["--help"]

ENV WEBSOCKET_PORT=9873
EXPOSE ${WEBSOCKET_PORT}

# Cant use ENV variables in CMD. Maybe we could use ARGS?
CMD ["--port", "9873", "--log_level", "20"]

# TODO: Hea;thcheck cuold actually use Python client to route ping-pong messages?
HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
    CMD netstat -an | grep ${WEBSOCKET_PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# docker build -t superlimitbreak/subscriptionserver2:latest .
# docker run --rm -it -p 9873:9873 superlimitbreak/subscriptionserver2:latest


# TODO: Add multistage build test
