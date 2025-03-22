#!/bin/bash
# Test script for Freqtrade Webhook Email Notifier with various authentication methods

# Get API key from .env file if it exists
if [ -f ".env" ]; then
  API_KEY=$(grep "API_KEY" .env | cut -d "=" -f2)
fi

# Get the authentication method from command line argument
AUTH_METHOD=${1:-query}  # Default to query auth if not specified

echo "Testing webhook with authentication method: $AUTH_METHOD"

BASE_URL="http://localhost:5001/webhook"

# Prepare the URL and authentication based on method
case $AUTH_METHOD in
  "query")
    if [ -n "$API_KEY" ]; then
      URL="$BASE_URL?token=$API_KEY"
    else
      URL="$BASE_URL"
    fi
    ;;
  "path")
    if [ -n "$API_KEY" ]; then
      URL="$BASE_URL/$API_KEY"
    else
      URL="$BASE_URL"
    fi
    ;;
  *)
    echo "Unknown authentication method: $AUTH_METHOD"
    echo "Supported methods: query, path"
    exit 1
    ;;
esac

echo "Sending test webhook to $URL"

# Basic buy signal test
curl -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "entry", 
    "exchange": "binance", 
    "pair": "BTC/USDT", 
    "side": "buy", 
    "order_type": "limit",
    "amount": 0.001, 
    "price": 50000, 
    "trade_id": 123456
  }'

echo -e "\n\nSending another test for sell signal..."

# Sell signal test
curl -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "exit", 
    "exchange": "binance", 
    "pair": "BTC/USDT", 
    "side": "sell", 
    "order_type": "limit",
    "amount": 0.001, 
    "price": 52000, 
    "profit_ratio": 0.04,
    "profit_abs": 20.0,
    "trade_id": 123456
  }' 