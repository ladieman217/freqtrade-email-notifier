#!/usr/bin/env python
"""
Unit tests for the Freqtrade Webhook Email Notifier
"""

import pytest
from fastapi.testclient import TestClient
import json
import os
from unittest.mock import patch, MagicMock

# Set test environment variables
os.environ["EMAIL_SENDER"] = "test@example.com"
os.environ["EMAIL_RECIPIENT"] = "recipient@example.com"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["API_KEY"] = "test_api_key"

# Import app after setting environment variables
from app import app

client = TestClient(app)

# Test data
valid_webhook = {
    "type": "entry",
    "exchange": "binance",
    "pair": "BTC/USDT",
    "side": "buy",
    "price": 50000,
    "amount": 0.001
}

invalid_webhook = {
    "exchange": "binance",
    "pair": "BTC/USDT",
    # Missing "type" field
}

# Tests

def test_index():
    """Test the index route"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "service": "Freqtrade Email Notifier"}

@patch('app.ses_client')
def test_webhook_valid_data_with_auth(mock_ses):
    """Test the webhook endpoint with valid data and authentication"""
    # Mock the SES client response
    mock_ses.send_email.return_value = {"MessageId": "test-message-id"}
    
    # Send a valid webhook with API key
    response = client.post(
        "/webhook",
        json=valid_webhook,
        headers={"X-API-Key": "test_api_key"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["messageId"] == "test-message-id"
    
    # Verify SES was called
    mock_ses.send_email.assert_called_once()

@patch('app.ses_client')
def test_webhook_valid_data_without_auth(mock_ses):
    """Test the webhook endpoint with valid data but missing authentication"""
    # Send a valid webhook without API key
    response = client.post(
        "/webhook",
        json=valid_webhook
    )
    
    # Should be unauthorized
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json()["detail"]
    
    # Verify SES was not called
    mock_ses.send_email.assert_not_called()

def test_webhook_invalid_data():
    """Test the webhook endpoint with invalid data"""
    # Send an invalid webhook with API key
    response = client.post(
        "/webhook",
        json=invalid_webhook,
        headers={"X-API-Key": "test_api_key"}
    )
    
    # Should be bad request
    assert response.status_code == 400
    assert "Missing 'type' field" in response.json()["detail"]

@patch('app.ses_client')
def test_webhook_service_error(mock_ses):
    """Test handling of service errors"""
    # Mock SES to raise an exception
    mock_ses.send_email.side_effect = Exception("Test error")
    
    # Send a valid webhook
    response = client.post(
        "/webhook",
        json=valid_webhook,
        headers={"X-API-Key": "test_api_key"}
    )
    
    # Should be internal server error
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]

# Run the tests when file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 