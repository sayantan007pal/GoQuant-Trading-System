import sys, types
import json
import numpy as np
import pytest
import plotly.graph_objs as go

# Stub dash_extensions to allow import in tests without installing the package
dash_ext = types.SimpleNamespace(
    EventSource=lambda *args, **kwargs: None,
    EventListener=lambda *args, **kwargs: None,
)
sys.modules['dash_extensions'] = dash_ext

from flask import Response
import app
from app import server, DEFAULT_SYMBOL, update_conn_status, update_metrics
from websocket_client import get_orderbook_queue


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

    queue = get_orderbook_queue(DEFAULT_SYMBOL)
    monkeypatch.setattr(queue, "get", fake_get)
    response = client.get(f"/stream?symbol={DEFAULT_SYMBOL}")
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
        paused=False,
        alert_open=False,
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


def test_update_stream_url():
    # Running this should start a listener thread and return correct SSE path
    url = app.update_stream_url('ETH-USDT-SWAP')
    assert url == '/stream?symbol=ETH-USDT-SWAP'


@pytest.mark.parametrize("vals,expected_open", [
    ((100, 0.3, 0.1, 1.0, 10), False),
    ((0, 0.3, 0.1, 1.0, 10), True),
    ((100, -1, 0.1, 1.0, 10), True),
    ((100, 0.3, -0.1, 1.0, 10), True),
    ((100, 0.3, 0.1, 0, 10), True),
    ((100, 0.3, 0.1, 1.0, 0), True),
])
def test_validate_inputs(vals, expected_open):
    msg, is_open = app.validate_inputs(*(vals))
    assert is_open == expected_open
    if expected_open:
        assert msg != ''
    else:
        assert msg == ''


def test_keyboard_shortcuts(monkeypatch):
    # Setup dummy histories
    app.price_history.extend([1, 2, 3])
    app.time_history.extend([1, 2, 3])
    app.latency_history.extend([1, 2, 3])

    # Toggle pause: initial False -> press 'p' -> True
    assert app.toggle_pause({'key': 'p'}, False) is True
    # Press other key leaves pause state unchanged
    assert app.toggle_pause({'key': 'x'}, True) is True

    # Reset charts: pressing 'r' clears histories
    app.reset_charts({'key': 'r'})
    assert len(app.price_history) == 0
    assert len(app.time_history) == 0
    assert len(app.latency_history) == 0

    # Toggle execution display store
    assert app.toggle_exec({'key': 't'}, True) is False
    assert app.toggle_exec({'key': 'a'}, False) is False

    # Toggle execution-chart style based on store
    assert app.toggle_exec_display(True) == {'display': 'block'}
    assert app.toggle_exec_display(False) == {'display': 'none'}