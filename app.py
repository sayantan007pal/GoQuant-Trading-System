"""
Dash-based dashboard for the GoQuant trade simulator.
"""
import time
from queue import Empty

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

import numpy as np
import plotly.graph_objs as go
from collections import deque
from datetime import datetime

from websocket_client import run_listener_in_thread, orderbook_queue
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

# History for mid-price chart
MAX_HISTORY = 200
price_history = deque(maxlen=MAX_HISTORY)
time_history = deque(maxlen=MAX_HISTORY)

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
        # Timer for periodic metric updates (interval in milliseconds)
        # Reduced interval for lower-latency UI updates
        dcc.Interval(id="interval-timer", interval=500, n_intervals=0),
        # Real-time Almgren–Chriss execution trajectory chart
        dbc.Row(
            dbc.Col(
                dcc.Graph(id="execution-chart", config={'displayModeBar': False}),
                width=12
            ),
            className="mt-4"
        ),
    ],
    fluid=True,
)

@app.callback(
    [dash.dependencies.Output(out_id, "children") for _, out_id in metrics]
    + [dash.dependencies.Output("execution-chart", "figure")],
    [dash.dependencies.Input("interval-timer", "n_intervals")],
    [
        dash.dependencies.State("input-quantity", "value"),
        dash.dependencies.State("input-volatility", "value"),
        dash.dependencies.State("input-feetier", "value"),
        dash.dependencies.State("input-lambda", "value"),
        dash.dependencies.State("input-horizon", "value"),
        dash.dependencies.State("input-steps", "value"),
    ],
)
def update_metrics(n, quantity_usd, volatility, fee_tier, risk_aversion, time_horizon, time_steps):
    # Fetch latest orderbook tick
    try:
        data, ts = orderbook_queue.get_nowait()
    except Empty:
        raise dash.exceptions.PreventUpdate

    bids = data.get("bids", [])
    asks = data.get("asks", [])
    if not bids or not asks:
        raise dash.exceptions.PreventUpdate

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    mid_price = 0.5 * (best_bid + best_ask)
    spread = best_ask - best_bid

    # Slippage estimation
    slippage = estimate_slippage(spread, quantity_usd / mid_price)
    # Fee estimation (assume taker)
    fees = calculate_fee(mid_price, quantity_usd / mid_price, fee_tier, is_taker=True)
    # Market impact estimation
    impact = almgren_chriss_impact(
        quantity=quantity_usd / mid_price,
        time_horizon=1.0,
        alpha=1.0,
        beta=1.0,
        gamma=0.05,
        eta=0.05,
        volatility=volatility,
        risk_aversion=0.001,
    )
    net_cost = slippage + fees + impact

    # Maker proportion prediction
    features = np.array([spread, quantity_usd / mid_price, volatility])
    maker_prop = predict_maker_proportion(features)

    # Internal latency measurement
    latency = timer.tick()

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
        trajectory = X * np.sinh(kappa * (T - times)) / np.sinh(kappa * T)
    else:
        trajectory = X * (1 - times / T)

    exec_fig = go.Figure(
        data=[go.Scatter(
            x=times,
            y=trajectory,
            mode="lines+markers",
            line=dict(color="magenta", width=2),
        )],
        layout=go.Layout(
            title="Optimal Execution Trajectory (Almgren–Chriss)",
            xaxis=dict(title="Time (t)"),
            yaxis=dict(title="Remaining Quantity"),
            margin=dict(l=40, r=20, t=40, b=40),
            template="plotly_dark",
        ),
    )

    return [
        f"{slippage:.2f}",
        f"{fees:.2f}",
        f"{impact:.2f}",
        f"{net_cost:.2f}",
        f"{maker_prop:.2%}",
        f"{latency:.1f}",
        exec_fig,
    ]

if __name__ == '__main__':
    app.run(debug=True)