import asyncio
import json
import threading
import time
from queue import Queue, Full

import websockets

"""
WebSocket client for streaming orderbook data with automatic reconnects and low-latency delivery.

Configurable ping settings detect dead connections quickly, and only the latest tick is kept to minimize processing delay.
"""
# Shared queue for the latest orderbook tick (keep only newest)
orderbook_queue = Queue(maxsize=1)

async def _ws_listener(uri: str):
    """
    Connect to the WebSocket URI and stream messages into a queue.
    Automatically reconnects on errors, using short ping intervals to detect issues.
    """
    # Settings for quick dead-connection detection and minimal buffering
    PING_INTERVAL = 5  # seconds between pings
    PING_TIMEOUT = 5   # seconds to wait for pong
    RECONNECT_DELAY = 1  # seconds to wait before reconnecting

    while True:
        try:
            async with websockets.connect(
                uri,
                ping_interval=PING_INTERVAL,
                ping_timeout=PING_TIMEOUT,
                compression=None,
            ) as websocket:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    timestamp = time.time()
                    try:
                        orderbook_queue.put((data, timestamp), block=False)
                    except Full:
                        # drop if the queue is full to keep only the latest tick
                        pass
        except Exception as exc:
            # suppress errors and retry after a short delay
            print(f"WebSocket connection error: {exc!r}. Reconnecting in {RECONNECT_DELAY}s...")
            await asyncio.sleep(RECONNECT_DELAY)

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