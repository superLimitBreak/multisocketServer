CONTAINER_TAG_SUBSCRIPTION_SERVER=superlimitbreak/subscriptionserver:latest

build:
	docker build --tag ${CONTAINER_TAG_SUBSCRIPTION_SERVER} .

push:
	docker push ${CONTAINER_TAG_SUBSCRIPTION_SERVER}

run:
	docker run -it --rm ${CONTAINER_TAG_SUBSCRIPTION_SERVER}

run_local:
	python3 subscription_server.py

clean:
	docker rmi ${CONTAINER_TAG_SUBSCRIPTION_SERVER}
