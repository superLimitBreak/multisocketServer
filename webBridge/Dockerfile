FROM python:alpine

ARG PYTHON_REQUIREMNTS=requirements.txt
COPY ${PYTHON_REQUIREMNTS} ${PYTHON_REQUIREMNTS}
RUN apk add --no-cache \
        --virtual .build-deps git &&\
    pip3 install --no-cache-dir -r ${PYTHON_REQUIREMNTS} &&\
    apk del .build-deps

COPY webBridge.py /

EXPOSE 10794

ENTRYPOINT ["python3", "webBridge.py"]
CMD ["--help"]

#HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
#    CMD netstat -an | grep ${PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# TODO: Add multistage build tests
