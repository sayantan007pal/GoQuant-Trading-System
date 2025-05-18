"""
Dash-based dashboard for the GoQuant trade simulator.
"""
import time
from queue import Empty

import dash
from dash import dcc, html, exceptions
import dash_bootstrap_components as dbc

import numpy as np
import plotly.graph_objs as go
from collections import deque
from datetime import datetime

from websocket_client import run_listener_in_thread, orderbook_queue
from flask import Response
import json
from dash_extensions import EventSource
from utils.latency_timer import LatencyTimer
from utils.fee_model import calculate_fee, FEE_TIERS
from models.slippage_model import estimate_slippage
from models.market_impact_model import almgren_chriss_impact
from models.maker_taker_model import predict_maker_proportion

# WebSocket endpoint for L2 orderbook (OKX BTC-USDT-SWAP)
WS_URI = 'wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP'
# Start background listener thread
run_listener_in_thread(WS_URI)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Timer for internal latency measurement
timer = LatencyTimer()

# History for mid-price and latency sparkline (rolling window)
MAX_HISTORY = 200
price_history = deque(maxlen=MAX_HISTORY)
time_history = deque(maxlen=MAX_HISTORY)
latency_history = deque(maxlen=MAX_HISTORY)

# Sidebar (input parameters)
sidebar = dbc.Card(
    [
        html.H5("Input Parameters", className="card-title"),
        html.Div([
            dbc.Label("Quantity (USD equivalent):", html_for="input-quantity"),
            dbc.Input(id="input-quantity", type="number", value=100),
        ], className="mb-3"),
        html.Div([
            dbc.Label("Volatility (σ):", html_for="input-volatility"),
            dbc.Input(id="input-volatility", type="number", value=0.3, step=0.01),
        ], className="mb-3"),
        html.Div([
            dbc.Label("Fee Tier:", html_for="input-feetier"),
            dbc.Select(
                id="input-feetier",
                options=[{"label": k, "value": k} for k in sorted(FEE_TIERS.keys())],
                value="Tier 0",
            ),
        ], className="mb-3"),
        html.Div([
            dbc.Label("Risk Aversion (λ):", html_for="input-lambda"),
            dbc.Input(id="input-lambda", type="number", value=0.001, step=1e-4),
        ], className="mb-3"),
        html.Div([
            dbc.Label("Execution Time Horizon (T):", html_for="input-horizon"),
            dbc.Input(id="input-horizon", type="number", value=1.0, step=0.1),
        ], className="mb-3"),
        html.Div([
            dbc.Label("Time Steps (N):", html_for="input-steps"),
            dbc.Input(id="input-steps", type="number", value=20, step=1),
        ], className="mb-3"),
    ],
    body=True,
    style={"height": "100%", "padding": "1rem"},
)

# Output metric cards
metrics = [
    ("Expected Slippage", "out-slippage"),
    ("Expected Fees", "out-fees"),
    ("Market Impact", "out-impact"),
    ("Net Cost", "out-netcost"),
    ("Maker Proportion", "out-maker"),
    ("Internal Latency (ms)", "out-latency"),
]

output_cards = []
for title, comp_id in metrics:
    output_cards.append(
        dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody(html.H4(id=comp_id, className="card-text")),
        ], style={"margin-bottom": "1rem"})
    )

content = dbc.Col(output_cards, width=9)

# App layout
app.layout = dbc.Container(
    [
        html.H2("GoQuant Trade Simulator", className="mt-4 mb-4"),
        dbc.Row([dbc.Col(sidebar, width=3), content]),
        # Server-sent events for push updates and status
        EventSource(id="sse", url="/stream"),
        dbc.Row(
            dbc.Col(html.Div("🟡 Connecting...", id="conn-status"), width=12),
        ),
        # Latency sparkline over rolling window
        dbc.Row(
            dbc.Col(
                dcc.Graph(id="latency-sparkline", config={'displayModeBar': False}),
                width=12,
            ),
            className="mb-4",
        ),
        # Real-time mid-price time series and orderbook depth charts
        dbc.Row([
            dbc.Col(
                dcc.Graph(id="price-chart", config={'displayModeBar': False}), width=6
            ),
            dbc.Col(
                dcc.Graph(id="depth-chart", config={'displayModeBar': False}), width=6
            ),
        ], className="mt-4"),
        # Real-time Almgren–Chriss execution trajectory chart
        dbc.Row(
            dbc.Col(
                dcc.Graph(id="execution-chart", config={'displayModeBar': False}), width=12
            ),
            className="mt-4",
        ),
    ],
    fluid=True,
)

@app.callback(
    [dash.dependencies.Output(out_id, "children") for _, out_id in metrics]
    + [
        dash.dependencies.Output("price-chart", "figure"),
        dash.dependencies.Output("depth-chart", "figure"),
        dash.dependencies.Output("execution-chart", "figure"),
        dash.dependencies.Output("latency-sparkline", "figure"),
    ],
    [dash.dependencies.Input("sse", "message")],
    [
        dash.dependencies.State("input-quantity", "value"),
        dash.dependencies.State("input-volatility", "value"),
        dash.dependencies.State("input-feetier", "value"),
        dash.dependencies.State("input-lambda", "value"),
        dash.dependencies.State("input-horizon", "value"),
        dash.dependencies.State("input-steps", "value"),
    ],
)
def update_metrics(
    message,
    quantity_usd,
    volatility,
    fee_tier,
    risk_aversion,
    time_horizon,
    time_steps,
):
    if not message:
        raise exceptions.PreventUpdate

    payload = json.loads(message)
    data = payload.get("data", {})
    ts = payload.get("timestamp")

    bids = data.get("bids", [])
    asks = data.get("asks", [])
    if not bids or not asks:
        raise exceptions.PreventUpdate

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    mid_price = 0.5 * (best_bid + best_ask)
    spread = best_ask - best_bid

    # record mid-price history
    time_history.append(datetime.fromtimestamp(ts))
    price_history.append(mid_price)

    # Slippage estimation
    slippage = estimate_slippage(spread, quantity_usd / mid_price)
    # Fee estimation (assume taker)
    fees = calculate_fee(mid_price, quantity_usd / mid_price, fee_tier, is_taker=True)
    # Market impact estimation
    impact = almgren_chriss_impact(
        quantity=quantity_usd / mid_price,
        time_horizon=time_horizon,
        alpha=1.0,
        beta=1.0,
        gamma=0.05,
        eta=0.05,
        volatility=volatility,
        risk_aversion=risk_aversion,
    )
    net_cost = slippage + fees + impact

    # Maker proportion prediction
    features = np.array([spread, quantity_usd / mid_price, volatility])
    maker_prop = predict_maker_proportion(features)

    # Internal latency measurement
    latency = timer.tick()
    latency_history.append(latency)

    # Build mid-price line chart
    price_fig = go.Figure(
        data=[
            go.Scatter(
                x=list(time_history),
                y=list(price_history),
                mode="lines",
                line=dict(color="cyan", width=2),
            )
        ],
        layout=go.Layout(
            title="Mid-Price Over Time",
            xaxis=dict(title="Time", type="date", tickformat="%H:%M:%S"),
            yaxis=dict(title="Mid Price"),
            margin=dict(l=40, r=20, t=40, b=40),
            template="plotly_dark",
        ),
    )

    # Build depth chart for top 10 levels
    top_n = 10
    bid_prices = [float(lvl[0]) for lvl in bids[:top_n]]
    bid_sizes = [float(lvl[1]) for lvl in bids[:top_n]]
    ask_prices = [float(lvl[0]) for lvl in asks[:top_n]]
    ask_sizes = [float(lvl[1]) for lvl in asks[:top_n]]
    depth_fig = go.Figure()
    depth_fig.add_trace(
        go.Bar(x=bid_prices, y=bid_sizes, name="Bids", marker_color="green", opacity=0.6)
    )
    depth_fig.add_trace(
        go.Bar(x=ask_prices, y=ask_sizes, name="Asks", marker_color="red", opacity=0.6)
    )
    depth_fig.update_layout(
        title="Orderbook Depth (Top 10 Levels)",
        xaxis=dict(title="Price"),
        yaxis=dict(title="Size"),
        barmode="overlay",
        margin=dict(l=40, r=20, t=40, b=40),
        template="plotly_dark",
    )

    # Compute real-time Almgren–Chriss execution trajectory
    X = quantity_usd / mid_price
    eta = 0.05
    sigma = volatility
    lam = risk_aversion
    T = time_horizon
    N = int(time_steps)
    times = np.linspace(0, T, N + 1)
    if eta > 0 and lam * sigma**2 > 0:
        kappa = np.sqrt(lam * sigma**2 / eta)
        traj = X * np.sinh(kappa * (T - times)) / np.sinh(kappa * T)
    else:
        traj = X * (1 - times / T)
    exec_fig = go.Figure(
        data=[
            go.Scatter(x=times, y=traj, mode="lines+markers", line=dict(color="magenta", width=2))
        ],
        layout=go.Layout(
            title="Optimal Execution Trajectory (Almgren–Chriss)",
            xaxis=dict(title="Time (t)"),
            yaxis=dict(title="Remaining Quantity"),
            margin=dict(l=40, r=20, t=40, b=40),
            template="plotly_dark",
        ),
    )

    # Build latency sparkline chart
    lat_fig = go.Figure(
        data=[
            go.Scatter(x=list(time_history), y=list(latency_history), mode="lines", line=dict(color="yellow", width=1))
        ],
        layout=go.Layout(
            title="Latency Over Time (ms)",
            xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(title="Latency (ms)", showgrid=False),
            margin=dict(l=40, r=20, t=40, b=20),
            template="plotly_dark",
            height=200,
        ),
    )

    return [
        f"{slippage:.2f}",
        f"{fees:.2f}",
        f"{impact:.2f}",
        f"{net_cost:.2f}",
        f"{maker_prop:.2%}",
        f"{latency:.1f}",
        price_fig,
        depth_fig,
        exec_fig,
        lat_fig,
    ]

# SSE endpoint for server-sent events (push updates)
@server.route('/stream')
def stream():
    def event_stream():
        while True:
            data, ts = orderbook_queue.get()
            payload = json.dumps({'data': data, 'timestamp': ts})
            yield f"data:{payload}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')


@app.callback(
    dash.dependencies.Output('conn-status', 'children'),
    [dash.dependencies.Input('sse', 'readyState'), dash.dependencies.Input('sse', 'error')]
)
def update_conn_status(ready_state, error):
    if error:
        return f"⚠️ Error: {error}"
    if ready_state == 0:
        return '🟡 Connecting...'
    if ready_state == 1:
        return '🟢 Connected'
    return '🔴 Disconnected'

if __name__ == '__main__':
    app.run(debug=True)