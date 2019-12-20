FROM python:alpine

WORKDIR /subscriptionServer2/webBridge

ARG PYTHON_REQUIREMNTS=requirements.txt
COPY ${PYTHON_REQUIREMNTS} .
RUN apk add --no-cache \
        --virtual .build-deps git &&\
    pip3 install --no-cache-dir -r ${PYTHON_REQUIREMNTS} &&\
    apk del .build-deps

COPY webBridge.py .

ARG PORT=10794
ENV PORT ${PORT}
EXPOSE ${PORT}

# --port=${PORT}"
ENTRYPOINT ["python3", "webBridge.py"]
CMD ["--help",]

#HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
#    CMD netstat -an | grep ${PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# TODO: Add multistage build tests
