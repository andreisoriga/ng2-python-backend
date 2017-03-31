import asyncio
import json

import aiohttp
from aiohttp import web


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    task = request.app.loop.create_task(send_handler(ws))

    print('websocket connection opened')

    async for msg in ws:

        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                json_data = json.loads(msg.data)
                print(json_data['message'])

                await ws.send_json(json_data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print(f'ws connection closed with exception {ws.exception()}')
        else:
            print(f"Received message {msg.type}:{msg.data} is not WSMsgType.TEXT")

    task.cancel()
    print('websocket connection closed')

    return ws


async def send_handler(ws):
    json_data = {'message': 'lifesign'}

    while True:
        await asyncio.sleep(10)
        await ws.send_json(json_data)


def setup_routes(app):
    app.router.add_get('/', websocket_handler)


loop = asyncio.get_event_loop()
app = web.Application(loop=loop)
setup_routes(app)
web.run_app(app, host='127.0.0.1', port=8765)
