import asyncio
import json
import threading
import time
from queue import Queue, Full

import websockets

# Shared queue for the latest orderbook tick
orderbook_queue = Queue(maxsize=1)

async def _ws_listener(uri: str):
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            timestamp = time.time()
            try:
                orderbook_queue.put((data, timestamp), block=False)
            except Full:
                # drop if the queue is full to keep only the latest tick
                pass

def _start_listener(uri: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_ws_listener(uri))

def run_listener_in_thread(uri: str):
    """
    Start the WebSocket listener in a background thread.
    """
    thread = threading.Thread(target=_start_listener, args=(uri,), daemon=True)
    thread.start()

# Example usage:
# run_listener_in_thread('wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP')