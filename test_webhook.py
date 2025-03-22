#!/usr/bin/env python
"""
Test script for Freqtrade Webhook Email Notifier
This script simulates different types of webhooks that Freqtrade might send
"""

import requests
import json
import time
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default server URL
DEFAULT_URL = "http://localhost:5001/webhook"
API_KEY = os.environ.get('API_KEY', '')

# Test webhook payloads
WEBHOOKS = {
    # Entry (buy) signal
    'entry': {
        "type": "entry",
        "exchange": "binance",
        "pair": "BTC/USDT",
        "side": "buy",
        "order_type": "limit",
        "amount": 0.001,
        "price": 50000,
        "trade_id": 123456
    },
    
    # Exit (sell) signal with profit
    'exit_profit': {
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
    },
    
    # Exit with loss
    'exit_loss': {
        "type": "exit",
        "exchange": "binance",
        "pair": "BTC/USDT",
        "side": "sell",
        "order_type": "market",
        "amount": 0.001,
        "price": 48000,
        "profit_ratio": -0.04,
        "profit_abs": -20.0,
        "trade_id": 123456
    },
    
    # Cancel order
    'cancel': {
        "type": "cancel",
        "exchange": "binance",
        "pair": "BTC/USDT",
        "trade_id": 123456,
        "reason": "timeout"
    },
    
    # Status update
    'status': {
        "type": "status",
        "status": "running",
        "timestamp": int(time.time())
    }
}

def send_webhook(url, payload, verbose=False, api_key=None, auth_method='query'):
    """Send webhook to specified URL"""
    if verbose:
        print(f"Sending webhook to {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
    
    headers = {"Content-Type": "application/json"}
    final_url = url
    
    # Apply authentication based on method
    if auth_method == 'query' and api_key:
        if '?' in url:
            final_url = f"{url}&token={api_key}"
        else:
            final_url = f"{url}?token={api_key}"
    elif auth_method == 'path' and api_key:
        final_url = f"{url}/{api_key}"
    
    if verbose:
        print(f"Final URL: {final_url}")
    
    try:
        response = requests.post(
            final_url,
            json=payload,
            headers=headers
        )
        
        if verbose:
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        
        return response.status_code, response.text
    except Exception as e:
        print(f"Error sending webhook: {str(e)}")
        return None, str(e)

def main():
    parser = argparse.ArgumentParser(description='Test Freqtrade Webhook Notifier')
    parser.add_argument('--url', type=str, default=DEFAULT_URL,
                        help=f'Webhook URL (default: {DEFAULT_URL})')
    parser.add_argument('--type', type=str, choices=list(WEBHOOKS.keys()) + ['all'],
                        default='all', help='Type of webhook to send (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--api-key', type=str, default=API_KEY,
                        help='API key for authentication')
    parser.add_argument('--auth-method', type=str, 
                        choices=['query', 'path'],
                        default='query',
                        help='Authentication method to use')
    
    args = parser.parse_args()
    
    if args.type == 'all':
        # Send all webhook types
        for name, payload in WEBHOOKS.items():
            print(f"\n=== Sending {name} webhook using {args.auth_method} auth ===")
            status, response = send_webhook(
                args.url, payload, args.verbose, args.api_key, 
                args.auth_method
            )
            if status:
                print(f"Result: {status} - {response}")
            time.sleep(1)  # Wait between requests
    else:
        # Send specific webhook type
        payload = WEBHOOKS[args.type]
        print(f"\n=== Sending {args.type} webhook using {args.auth_method} auth ===")
        status, response = send_webhook(
            args.url, payload, args.verbose, args.api_key, 
            args.auth_method
        )
        if status:
            print(f"Result: {status} - {response}")

if __name__ == "__main__":
    main() 