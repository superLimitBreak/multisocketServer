import asyncio
import websockets
import umsgpack

async def hello():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        data = {'hello': 'world'}
        await websocket.send(umsgpack.dumps(data))
        msg = umsgpack.loads(await websocket.recv())
        print(msg)
asyncio.get_event_loop().run_until_complete(hello())
