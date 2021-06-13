udp2ws
======

python3 asyncio server that forwards UDP traffic to all clients connected via WebSockets.

This concept was born from the use-case to send ArtNet UDP packets to a web-browser. 
This concept could be used for any UDP data.

I could make this support multiple sockets as a ws path ... humm ...
In future we could support bi-directional travel ws2udp, but that would need to know about a destination UDP address. I think keeping this uni-directional for now is fine.

* Similar Ideas
    * [Assetto Corsa - udp2ws - UDP to WebSockets bridge](https://www.racedepartment.com/downloads/udp2ws-udp-to-websockets-bridge.19909/)
        * Used for a race api

