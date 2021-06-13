FROM python:alpine
RUN pip install websockets
COPY udp2ws.py .
ENTRYPOINT ["python3", "udp2ws.py"]
