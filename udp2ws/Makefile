build:
	docker build --tag udp2ws .
run:
	docker run --rm -it \
		-p 9001:9001/udp \
		-p 9002:9002 \
		udp2ws \
			--udp_port 9001 \
			--ws_port 9002
