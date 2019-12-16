FROM python:alpine as base

ARG WORKDIR=/subscriptionServer2
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

FROM base as code
COPY \
    __init__.py \
    client.py \
    server.py \
./

# Test -------------------------------------------------------------------------

FROM base as base_test
RUN pip3 install --no-cache-dir pytest
FROM base_test as test
COPY --from=code ${WORKDIR}/ ${WORKDIR}/
COPY \
    tests/* \
./tests/
RUN pytest

# Prod -------------------------------------------------------------------------

FROM code as production
ENV WEBSOCKET_PORT=9873
EXPOSE ${WEBSOCKET_PORT}
ENTRYPOINT ["python3", "server.py"]
CMD ["--port", "9873", "--log_level", "20"]
#CMD ["--help"]
# Cant use ENV variables in CMD. Maybe we could use ARGS?

# TODO: Healthcheck could actually use Python client to route ping-pong messages?
COPY client_healthcheck.py ./
HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
    CMD netstat -an | grep ${WEBSOCKET_PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;
