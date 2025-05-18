 # GoQuant Trading System

 This project is a high-performance trade simulator leveraging real-time market data to estimate transaction costs and market impact. It connects to WebSocket endpoints streaming full L2 orderbook data for cryptocurrency exchanges.

 ## Features
 - Real-time L2 orderbook ingestion via WebSocket
- Configurable execution parameters: exchange, symbol (picker), order type, quantity, volatility, fee tier
 - Output metrics: expected slippage, fees, market impact (Almgren–Chriss), net cost, maker/taker proportion, internal latency
- Interactive dashboard UI (Dash) with:
  - Dynamic symbol picker for live data feed
  - Real-time input validation for parameters
  - Keyboard shortcuts: `p`=pause/resume, `r`=reset charts, `t`=toggle execution chart
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

## Demo
<img width="1352" alt="Screenshot 2025-05-19 at 2 15 05 AM" src="https://github.com/user-attachments/assets/aaadf01b-9bbb-46d6-baf0-4f6643a2e892" />
<img width="1352" alt="Screenshot 2025-05-19 at 2 11 58 AM" src="https://github.com/user-attachments/assets/76a253e1-400f-4724-bfa4-06fb954ed229" />
<img width="1352" alt="Screenshot 2025-05-19 at 1 27 17 AM" src="https://github.com/user-attachments/assets/63e5d488-b07d-45a3-9eac-72bb8a896a3b" />
<img width="1352" alt="Screenshot 2025-05-19 at 1 26 20 AM" src="https://github.com/user-attachments/assets/6a473e0c-64f0-4894-9811-0cdac538f82d" />

 ## Documentation
See `docs/design.md` for architecture and model descriptions (including Phase 2 UI enhancements), `docs/debugging.md` for using the interactive debug toolbar, and `docs/setup.md` for initial VPN and OKX API setup instructions.

### Real-Time Almgren–Chriss Execution Visualization

The dashboard now integrates a live Almgren–Chriss optimal execution model. In the sidebar, you can also:
- Select the **Symbol** (trading pair) to switch live data feeds
- See real-time **input validation** feedback for all numeric parameters
- Use **keyboard shortcuts**:
  - `p` to pause/resume live updates
  - `r` to reset all chart histories
  - `t` to toggle the execution trajectory chart
Adjust the **Risk Aversion (λ)**, **Execution Time Horizon (T)**, and **Time Steps (N)** inputs to visualize the optimal trade schedule update in real time based on current orderbook conditions.
