import asyncio
import json

import aiohttp
from aiohttp import web


class WebSocketService:

    def __init__(self, request):
        self.request = request
        self.ws = web.WebSocketResponse()

        self.status = False

        self.consumer_queue = asyncio.Queue()
        self.producer_queue = asyncio.Queue()

    async def start(self):
        await self.ws.prepare(self.request)

        task = self.request.app.loop.create_task(self.producer())

        print('websocket connection opened')
        self.status = True

        try:
            async for msg in self.ws:

                if msg.type == aiohttp.WSMsgType.TEXT:

                    json_data = json.loads(msg.data)

                    if json_data['message'] == 'close_connection':
                        task.cancel()
                        await self.ws.close()
                    else:
                        print(json_data['message'])

                        await self.consumer(json_data)

                        await self.send(json_data)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f'ws connection closed with exception {self.ws.exception()}')
                else:
                    print(f"Received message {msg.type}:{msg.data} is not WSMsgType.TEXT")
        except asyncio.CancelledError:
            # we are closing the socket anyway, so pass on
            pass

        task.cancel()
        print('websocket connection closed')
        self.status = False

        return self.ws

    async def producer(self):
        json_data = {'message': 'lifesign'}

        while True:
            await asyncio.sleep(10)
            await self.ws.send_json(json_data)

    async def consumer(self, data):
        print('adding to consumer Queue')
        await self.consumer_queue.put(data)
        print(f'consumer.queue has {self.consumer_queue.qsize()} size.')

    async def send(self, data):
        await self.ws.send_json(data)


async def websocket_handler(request):
    request.app['wb'] = WebSocketService(request)
    return await request.app['wb'].start()


async def send_handler(request):
    if 'wb' in request.app and request.app['wb'].status:
        await request.app['wb'].send({'message': 'from the send method'})
        return web.Response()

    return web.Response(status=500)


def setup_routes(app):
    app.router.add_get('/', websocket_handler)
    app.router.add_get('/send', send_handler)


loop = asyncio.get_event_loop()
app = web.Application(loop=loop)
setup_routes(app)
web.run_app(app, host='127.0.0.1', port=8765)
