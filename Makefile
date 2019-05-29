
.PHONY: build
build:
	${MAKE} $@ --directory server
	${MAKE} $@ --directory webBridge

.PHONY: push
push:
	${MAKE} $@ --directory server
	${MAKE} $@ --directory webBridge

.PHONY: clean
clean:
	${MAKE} $@ --directory server
	${MAKE} $@ --directory webBridge
