CONTAINER_TAG_WEB_BRIDGE=superlimitbreak/subscriptionserver_bridge:latest


client_reconnect.py:
	cp ../client/python/client_reconnect.py ./

build: client_reconnect.py
	docker build --tag ${CONTAINER_TAG_WEB_BRIDGE} .

run:
	docker run -it --rm ${CONTAINER_TAG_WEB_BRIDGE}

run_local:
	python3 webBridge.py

clean:
	rm -rf client_reconnect.py
