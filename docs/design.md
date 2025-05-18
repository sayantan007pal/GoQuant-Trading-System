# GoQuant Trading System Design Document

## Overview
This document outlines the architecture and design decisions for the GoQuant trade simulator, including module responsibilities, data flow, and model descriptions.

## Architecture

```
------------------------------------------+
|                  app.py                  |  <-- Dash application (UI + callbacks)
|------------------------------------------|
|  websocket_client.py                    |  <-- Background WebSocket listener
|------------------------------------------|
|  models/                                |  <-- Calculation models
|    - slippage_model.py                  |
|    - market_impact_model.py             |
|    - maker_taker_model.py               |
|------------------------------------------|
|  utils/                                 |  <-- Helper utilities
|    - fee_model.py                       |
|    - latency_timer.py                   |
------------------------------------------+
```

### Data Flow
1. `websocket_client.py` connects to L2 orderbook stream and pushes the latest tick into a queue.
2. Dash `dcc.Interval` triggers a callback in `app.py` to pull from the queue.
3. On each tick:
   - Compute spread and mid-price from orderbook data.
   - Invoke models:
     - Slippage estimation (linear/quantile regression placeholder).
     - Fees calculation (rule-based tier model).
     - Market impact (Almgren–Chriss framework).
     - Maker/Taker proportion (logistic regression placeholder).
   - Measure processing latency via `LatencyTimer`.
4. Update UI components with computed metrics.

## Model Descriptions

### Slippage Model
Simple linear regression placeholder: slippage ∝ spread × quantity.

### Market Impact Model
Almgren–Chriss-based cost components:
- Temporary Impact: η * (Q / T)^α
- Permanent Impact: γ * (Q / T)^β
- Risk Term: 0.5 * λ * σ² * Q² / T

### Maker/Taker Proportion
Logistic regression placeholder:
`P(maker) = sigmoid(wᵀx + b)`

### Fee Model
Static fee rates per tier. Users must configure based on exchange documentation.

## Almgren–Chriss Model Demonstration

The demo script `docs/almgren_chriss_demo.py` visualizes the optimal execution schedule under the Almgren–Chriss framework. It illustrates how different risk aversion (λ) values influence the trade execution trajectory over a normalized time horizon.

```bash
python docs/almgren_chriss_demo.py
```

Open the generated HTML file (`docs/almgren_chriss_demo.html`) in your browser to explore the interactive chart of execution schedules.

## Next Steps
- Integrate regression training pipelines for slippage and maker/taker models.
- Parameterize fee tier mapping with live exchange data.
- Extend UI for multiple symbols and advanced settings.