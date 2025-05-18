"""
Utility for measuring internal processing latency.
"""
import time

class LatencyTimer:
    """
    Tracks elapsed time between ticks to measure latency in milliseconds.
    """
    def __init__(self):
        self._last = time.time()

    def tick(self) -> float:
        """
        Compute latency since last tick in milliseconds.

        :return: elapsed time in milliseconds
        """
        now = time.time()
        latency_ms = (now - self._last) * 1000.0
        self._last = now
        return latency_ms