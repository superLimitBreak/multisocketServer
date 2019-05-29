FROM python:alpine
RUN pip install falcon
COPY client_reconnect.py webBridge.py /

ENV PORT=8000
ENV subscription_server_hostname=localhost:9872
ENTRYPOINT ["python3", "webBridge.py"]
#CMD ["--help"]
# Cant use ENV's in CMD. Maybe we can use ARGS?
CMD ["--port", "8000", "--subscription_server_hostname", "9872"]

HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
    CMD netstat -an | grep ${PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# docker build -t falcon_url_to_subscription_bridge --file falcon_url_to_subscription_bridge.dockerfile .
# docker run --rm -it -p 8000:8000 falcon_url_to_subscription_bridge


# TODO: Add multistage build tests
