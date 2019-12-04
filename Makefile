PATH_SERVER=subscriptionServer2/server
PATH_WEB_BRIDGE=webBridge

.PHONY: build
build:
	${MAKE} $@ --directory ${PATH_SERVER}
	#${MAKE} $@ --directory ${PATH_WEB_BRIDGE}  # temp

.PHONY: push
push:
	${MAKE} $@ --directory ${PATH_SERVER}
	#${MAKE} $@ --directory ${PATH_WEB_BRIDGE}

.PHONY: cloc
cloc:
	cloc --vcs=git

.PHONY: clean
clean:
	${MAKE} $@ --directory ${PATH_SERVER}
	#${MAKE} $@ --directory ${PATH_WEB_BRIDGE}
