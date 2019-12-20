CONTAINER_TAG_WEB_BRIDGE=superlimitbreak/subscriptionserver_bridge:latest

build:
	docker build --tag ${CONTAINER_TAG_WEB_BRIDGE} .

push:
	docker push ${CONTAINER_TAG_WEB_BRIDGE}

run:
	docker run -it --rm ${CONTAINER_TAG_WEB_BRIDGE}

debug:
	cd ../../superLimitBreakSetup && \
	docker-compose down && \
	docker-compose build subscriptionserver_bridge && \
	docker-compose run --service-ports \
		--entrypoint "python3 webBridge.py ws://subscriptionserver:9873 --port 10794" \
		subscriptionserver_bridge

run_local:
	python3 webBridge.py ws://localhost:9873 --port 10794

clean:
	docker rmi ${CONTAINER_TAG_WEB_BRIDGE}
