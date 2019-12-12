CONTAINER_TAG_SUBSCRIPTION_SERVER=superlimitbreak/subscriptionserver2:latest

build:
	docker build --tag ${CONTAINER_TAG_SUBSCRIPTION_SERVER} .

push:
	docker push ${CONTAINER_TAG_SUBSCRIPTION_SERVER}

run:
	docker run -it --rm -p 9873:9873 ${CONTAINER_TAG_SUBSCRIPTION_SERVER}

shell:
	docker run -it --rm -p 9873:9873 --entrypoint /bin/sh ${CONTAINER_TAG_SUBSCRIPTION_SERVER}

run_local:
	python3 subscription_server.py

clean:
	docker rmi ${CONTAINER_TAG_SUBSCRIPTION_SERVER}
