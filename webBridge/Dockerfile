FROM python:alpine
RUN pip install falcon
COPY client_reconnect.py webBridge.py /

EXPOSE 10794

ENTRYPOINT ["python3", "webBridge.py"]
CMD ["--help"]

#HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
#    CMD netstat -an | grep ${PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# TODO: Add multistage build tests
