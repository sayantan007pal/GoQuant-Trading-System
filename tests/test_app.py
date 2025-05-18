import json
import numpy as np
import pytest
import plotly.graph_objs as go

from flask import Response

import app
from app import server, orderbook_queue, update_conn_status, update_metrics


@pytest.fixture
def client():
    return server.test_client()


def test_sse_stream(client, monkeypatch):
    # Prepare a dummy tick and then stop iteration
    dummy_data = {"bids": [["100", "1"]], "asks": [["101", "2"]]}
    dummy_ts = 12345.6
    calls = {"count": 1}

    def fake_get():
        if calls["count"] > 0:
            calls["count"] -= 1
            return dummy_data, dummy_ts
        raise StopIteration

    monkeypatch.setattr(orderbook_queue, "get", fake_get)
    response = client.get("/stream")
    # Read only the first SSE event from the streaming response
    # Consume only the first SSE event from the streaming response
    it = response.response
    first = next(it)
    assert first.startswith(b"data:")
    # Extract JSON payload
    payload = json.loads(first.decode().split("\n\n")[0][5:])
    assert payload["data"] == dummy_data
    assert payload["timestamp"] == dummy_ts


@pytest.mark.parametrize(
    "state,error,expected",
    [
        (0, None, "🟡 Connecting..."),
        (1, None, "🟢 Connected"),
        (2, None, "🔴 Disconnected"),
        (1, "oops", "⚠️ Error: oops"),
    ],
)
def test_update_conn_status(state, error, expected):
    assert update_conn_status(state, error) == expected


def test_update_metrics(monkeypatch):
    # Simulate incoming SSE message content
    dummy_data = {"bids": [["100", "1"]], "asks": [["101", "1"]]}
    dummy_ts = 1610000000.0
    payload = {"data": dummy_data, "timestamp": dummy_ts}
    message = json.dumps(payload)

    # Monkey-patch timer to return fixed latency
    class DummyTimer:
        def tick(self):
            return 42.0

    monkeypatch.setattr(app, "timer", DummyTimer())

    # Call update_metrics with known parameters
    outputs = update_metrics(
        message,
        quantity_usd=100.0,
        volatility=0.5,
        fee_tier="Tier 0",
        risk_aversion=0.1,
        time_horizon=1.0,
        time_steps=2,
    )
    # Expect 10 outputs: 6 metrics + 4 figures
    assert isinstance(outputs, list) and len(outputs) == 10
    slippage, fees, impact, net_cost, maker_prop, latency_str, price_fig, depth_fig, exec_fig, lat_fig = outputs
    # Numeric metrics should be strings ending with decimals
    assert isinstance(slippage, str)
    assert isinstance(fees, str)
    assert isinstance(impact, str)
    assert isinstance(net_cost, str)
    assert isinstance(maker_prop, str) and maker_prop.endswith("%")
    assert isinstance(latency_str, str) and latency_str.startswith("42.0")
    # Figures should be plotly Figure instances
    for fig in (price_fig, depth_fig, exec_fig, lat_fig):
        assert isinstance(fig, go.Figure)