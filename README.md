# Freqtrade Email Notifier

A Python service that receives Freqtrade webhooks and sends email notifications using AWS SES.

[中文文档](README_zh.md)

## Features

- Receives webhooks from Freqtrade trading bot
- Sends formatted email notifications using AWS SES
- Supports both plain text and HTML email formats
- Built with FastAPI for high performance and async processing
- Configurable via environment variables
- Automatic API documentation (Swagger UI)
- API key authentication for enhanced security
- Containerized with Docker for easy deployment
- Custom strategy messages support for advanced notifications

## Requirements

- Python 3.7+
- AWS account with SES service configured
- Verified email addresses in SES (for sender email)

## Quick Start with Docker

The easiest way to run the service is using Docker:

```bash
# Clone the repository
git clone https://github.com/yourusername/freqtrade-email-notifier.git
cd freqtrade-email-notifier

# Create .env file
cp .env.example .env
# Edit the .env file with your AWS credentials and email configuration

# Start the service with Docker Compose
docker-compose up -d
```

## Setup with Virtual Environment

### Linux/Mac

1. Clone this repository
2. Use the setup script to create a virtual environment and install dependencies:
```
chmod +x setup.sh
./setup.sh
```
3. The script will:
   - Create a virtual environment in the `venv` directory
   - Install all required dependencies
   - Create a `.env` file from `.env.example` if it doesn't exist

4. Edit the `.env` file with your AWS credentials and email configuration
5. Make sure your sender email is verified in AWS SES

### Windows

1. Clone this repository
2. Use the setup script to create a virtual environment and install dependencies:
```
setup.bat
```
3. The script will:
   - Create a virtual environment in the `venv` directory
   - Install all required dependencies
   - Create a `.env` file from `.env.example` if it doesn't exist

4. Edit the `.env` file with your AWS credentials and email configuration
5. Make sure your sender email is verified in AWS SES

## Configuration

The application uses environment variables for configuration. Copy the `.env.example` file to `.env` and configure the following:

### Email Configuration
- `EMAIL_SENDER`: Your verified SES sender email address
- `EMAIL_RECIPIENT`: The email address to receive notifications

### AWS Configuration
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: AWS region where your SES service is configured

### Security Configuration
- `API_KEY`: Secret key for webhook endpoint authentication (leave empty to disable authentication)

### Server Configuration
- `PORT`: Server port (default: 5001)

## Running the Service

### Using Docker:

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Using the run script:

Linux/Mac:
```
chmod +x run.sh
./run.sh
```

Windows:
```
run.bat
```

### Manual start:

1. Activate the virtual environment (if not already activated):
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

2. Start the service:
```
python app.py
```

For production deployment, you can use:

```
uvicorn app:app --host 127.0.0.1 --port 5001
```

## API Documentation

FastAPI automatically generates interactive API documentation. After starting the server, visit:

- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

## Custom Strategy Messages

The service supports receiving custom messages from your trading strategy, allowing you to send notifications about market conditions, indicator values, or any other information from your strategy code.

### Example Use Cases

- Send alerts when key technical indicators cross thresholds
- Notify about changing market conditions
- Send periodic performance reports
- Alert about portfolio allocation changes
- Send debugging information during strategy development

### Configuration

In your Freqtrade configuration, enable custom messages:

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook",
    "format": "json",
    "allow_custom_messages": true,
    "strategy_msg": {
        "type": "strategy_msg",
        "msg": "{msg}"
    }
}
```

### Sending Custom Messages from Strategy

Custom messages can be sent from your strategy using the `self.dp.send_msg()` method. Your message can be:

1. **Plain text string**:
```python
self.dp.send_msg({'type': 'strategy_msg', 'msg': 'BTC trend has changed to bullish'})
```

2. **Structured data (dictionary)**:
```python
self.dp.send_msg({
    'type': 'strategy_msg',
    'msg': {
        'pair': 'BTC/USDT',
        'indicator': 'RSI',
        'value': 25.3,
        'action': 'Buy signal generated',
        'current_price': 38750.45
    }
})
```

3. **Lists or other JSON-serializable data**:
```python
self.dp.send_msg({
    'type': 'strategy_msg',
    'msg': [
        {'pair': 'BTC/USDT', 'trend': 'bullish', 'signal': 'buy'},
        {'pair': 'ETH/USDT', 'trend': 'bearish', 'signal': 'sell'}
    ]
})
```

### Integration Points

You can send custom messages from any of these strategy methods:

- `populate_indicators()` - for technical indicator alerts
- `populate_buy_trend()` - for buy signal notifications
- `populate_sell_trend()` - for sell signal notifications
- `bot_loop_start()` - for periodic status updates

For a complete example configuration and integration code, refer to the `freqtrade_webhook_config.json` file included in this repository.

## Freqtrade Configuration

In your Freqtrade configuration file, add the webhook URL:

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook",
    "format": "json"
}
```

If you have enabled API key authentication, you have two options:

### 1. URL Query Parameter Authentication (Recommended)

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook?token=your_secret_api_key",
    "format": "json"
}
```

### 2. Path-based Authentication

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook/your_secret_api_key",
    "format": "json"
}
```

## Security Considerations

- Always use HTTPS in production environments
- Set a strong API key if enabling authentication
- Never commit your `.env` file to version control
- Ensure your AWS credentials have the minimum required permissions
- Configure SES with proper sending limits to avoid unexpected costs

## Testing

### Unit Tests

Run the unit tests with:

```bash
# Using pytest directly
pytest tests/ -v

# Or using the test script
./run_tests.sh
```

### Integration Tests

You can test the webhook endpoint using curl:

```
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secret_api_key" \
  -d '{"type":"entry","exchange":"binance","pair":"BTC/USDT","side":"buy","price":20000,"amount":0.05}'
```

Or use the included test script:

```bash
# Test all webhook types
python test_webhook.py --verbose

# Test specific webhook type
python test_webhook.py --type entry --verbose

# Test custom message types
python test_webhook.py --type strategy_msg_dict --verbose
python test_webhook.py --type strategy_msg_string --verbose
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.