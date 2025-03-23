#!/bin/bash
# Script to run tests for Freqtrade Webhook Email Notifier

# Activate virtual environment
source .venv/bin/activate

# Run unit tests
echo "Running unit tests..."
pytest tests/ -v

# Run webhook integration tests
echo -e "\nRunning webhook integration tests..."
python test_webhook.py --verbose

echo -e "\nTests completed. Check your email to verify if notifications were sent correctly." 