import asyncio
import websockets
import umsgpack

data = {
    'action': 'message',
    'data': [
        {
            "deviceid": "main",
            "func": "text.html_bubble",
            "html": "<h1>Ready Steady Go</h1><p>Fullmetal Alchemist (Opening 2)</p><p>L'Arc-en-Ciel</p><p>Translation: Matt</p>",
        },
    ],
}

async def hello():
    uri = "ws://localhost:9873"
    async with websockets.connect(uri) as websocket:
        await websocket.send(umsgpack.dumps(data))
        #msg = umsgpack.loads(await websocket.recv())
        #print(msg)
asyncio.get_event_loop().run_until_complete(hello())
