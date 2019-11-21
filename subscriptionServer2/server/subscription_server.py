import asyncio
import websockets
import umsgpack

import logging
log = logging.getLogger(__name__)

clients = set()

async def echo(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            for client in clients:
                await client.send(message)
    except Exception:
        log.exception('Its broken')
    finally:
        clients.remove(websocket)

start_server = websockets.serve(echo, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
