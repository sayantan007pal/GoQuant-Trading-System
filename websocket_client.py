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
# Mapping from symbol to latest-orderbook queue (keep only newest tick)
orderbook_queues = {}

def get_orderbook_queue(symbol: str) -> Queue:
    """Get or create the queue for the given symbol."""
    if symbol not in orderbook_queues:
        orderbook_queues[symbol] = Queue(maxsize=1)
    return orderbook_queues[symbol]

async def _ws_listener(uri: str, queue: Queue):
    """
    Connect to the WebSocket URI and stream messages into the given queue.
    Automatically reconnects on errors, using short ping intervals to detect issues.
    """
    PING_INTERVAL = 5   # seconds between pings
    PING_TIMEOUT = 5    # seconds to wait for pong
    RECONNECT_DELAY = 1 # seconds to wait before reconnecting

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
                        queue.put((data, timestamp), block=False)
                    except Full:
                        pass
        except Exception as exc:
            print(f"WebSocket connection error: {exc!r}. Reconnecting in {RECONNECT_DELAY}s...")
            await asyncio.sleep(RECONNECT_DELAY)

def _start_listener(uri: str, queue: Queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_ws_listener(uri, queue))

def run_listener_for_symbol(symbol: str):
    """
    Start a listener thread for the given symbol if not already started.
    """
    queue = get_orderbook_queue(symbol)
    uri = f"wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/{symbol}"
    thread_name = f"ws-{symbol}"
    if not any(t.name == thread_name for t in threading.enumerate()):
        thread = threading.Thread(
            target=_start_listener,
            args=(uri, queue),
            daemon=True,
            name=thread_name,
        )
        thread.start()

# Example usage:
# run_listener_in_thread('wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP')