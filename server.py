#!/usr/bin/env python

import asyncio
import websockets


class EventBus():

    def __init__(self, loop):
        self.incoming = asyncio.Queue()
        self.outgoing = asyncio.Queue()

    async def consume(self, message):
        print(message)
        msg_to_consume = await self.incoming.get()
        # do something 'consuming' :)
        consume_output = msg_to_consume
        await self.outgoing.put(consume_output)

    async def produce(self):
        # await asyncio.sleep(10)
        # return '{"message": "lifesign"}'
        msg_out = await self.outgoing.get()
        return msg_out



async def consumer(message):
    print(message)


async def producer():
    await asyncio.sleep(10)
    return '{"message": "lifesign"}'


async def handler(websocket, path):
    while True:
        listener_task = asyncio.ensure_future(websocket.recv())
        producer_task = asyncio.ensure_future(producer())
        done, pending = await asyncio.wait(
            [listener_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED)

        if listener_task in done:
            message = listener_task.result()
            await consumer(message)
        else:
            listener_task.cancel()

        if producer_task in done:
            message = producer_task.result()
            await websocket.send(message)
        else:
            producer_task.cancel()

start_server = websockets.serve(handler, 'localhost', 8765)

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(start_server)
    loop.run_forever()
except KeyboardInterrupt:  # pragma: no branch
    pass
finally:
    # Stop loop:
    loop.stop()

    # Find all running tasks:
    pending = asyncio.Task.all_tasks()

    # Run loop until tasks done:
    try:
        loop.run_until_complete(asyncio.gather(*pending))
    except asyncio.CancelledError:
        pass

    print("Shutdown complete ...")

loop.close()
