 # GoQuant Trading System

 This project is a high-performance trade simulator leveraging real-time market data to estimate transaction costs and market impact. It connects to WebSocket endpoints streaming full L2 orderbook data for cryptocurrency exchanges.

 ## Features
 - Real-time L2 orderbook ingestion via WebSocket
 - Configurable execution parameters: exchange, symbol, order type, quantity, volatility, fee tier
 - Output metrics: expected slippage, fees, market impact (Almgren–Chriss), net cost, maker/taker proportion, internal latency
 - Interactive dashboard UI (Dash)
 - Modular code architecture for models and utilities

 ## Installation

 ```bash
 # Create and activate a virtual environment (optional but recommended)
 python3 -m venv venv
 source venv/bin/activate

 # Install dependencies
 pip install -r requirements.txt
 ```

 ## Usage

 ```bash
 python app.py
 ```

 Then open http://127.0.0.1:8050 in your browser to access the dashboard.

 ## Project Structure

 ```
 .
 ├── README.md
 ├── requirements.txt
 ├── app.py
 ├── websocket_client.py
 ├── models/
 │   ├── slippage_model.py
 │   ├── market_impact_model.py
 │   └── maker_taker_model.py
 ├── utils/
 │   ├── fee_model.py
 │   └── latency_timer.py
 └── docs/
     └── design.md
 ```

 ## Documentation
 See `docs/design.md` for architecture, model descriptions, and implementation details.