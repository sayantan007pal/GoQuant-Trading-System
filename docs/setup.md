# Setup Instructions for OKX API Access

## VPN Configuration

OKX SPOT exchange market data endpoints may be geo-restricted. To ensure connectivity:
1. Install and configure a VPN client (e.g., OpenVPN, NordVPN, or any corporate VPN).
2. Connect to a region where OKX is accessible (for example, a US or EU server).
3. Verify access by querying a public market-data endpoint:
   ```bash
   curl -s 'https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT' | jq .
   ```

No OKX account is required to retrieve public market data.

## Review OKX SPOT API Documentation

Familiarize yourself with the public REST API endpoints for market data:

- **OKX API Reference (Market Data)**
  https://www.okx.com/docs-v5/en/#rest-api-market-data
- **L2 Orderbook (25 levels)**
  https://www.okx.com/docs-v5/en/#rest-api-market-data-get-l2-25-instrument

Use these endpoints to understand available fields, rate limits, and data formats before integrating live streams.