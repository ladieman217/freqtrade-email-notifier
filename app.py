from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import boto3
import json
import os
import uvicorn
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler(
            'app.log', 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )  # File output with rotation
    ]
)
logger = logging.getLogger("freqtrade-notifier")

app = FastAPI(title="Freqtrade Email Notifier")

# Configuration
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'your-sender@example.com')
EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', 'your-recipient@example.com')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
API_KEY = os.environ.get('API_KEY', '')

# Log configuration on startup
logger.info(f"Starting Freqtrade Email Notifier")
logger.info(f"Email sender: {EMAIL_SENDER}")
logger.info(f"Email recipient: {EMAIL_RECIPIENT}")
logger.info(f"AWS Region: {AWS_REGION}")
logger.info(f"API Key configured: {bool(API_KEY)}")

# Initialize boto3 SES client
ses_client = boto3.client('ses', region_name=AWS_REGION)

# API Key verification function
async def verify_api_key(token: Optional[str] = None):
    """
    Verify API key from query parameter
    """
    if not API_KEY:
        # If no API key is configured, don't require authentication
        return True
    
    # Check query parameter
    if token and token == API_KEY:
        return True
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key",
    )

# Common webhook processing function
async def process_webhook_data(webhook_data: dict):
    """
    Process webhook data, create and send email notification based on Freqtrade webhook types
    """
    # Validate input data
    if not isinstance(webhook_data, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook data format")
    
    # Determine webhook type
    webhook_type = webhook_data.get('type')
    if not webhook_type:
        raise HTTPException(status_code=400, detail="Missing 'type' field in webhook data")
    
    # Log the received webhook
    logger.info(f"Received webhook type: {webhook_type}")
    logger.debug(f"Webhook data: {json.dumps(webhook_data, indent=2)}")
    
    # Prepare subject based on webhook type
    subject = f"Freqtrade Alert - {webhook_type}"
    
    # Common header for all email types
    body_text = f"Freqtrade Trading Bot Alert\n\n"
    body_text += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    body_text += f"Type: {webhook_type}\n\n"
    
    body_html = f"""
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; }}
        .trade-info {{ margin-bottom: 20px; }}
        .data-section {{ margin-top: 30px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
      </style>
    </head>
    <body>
      <h1>Freqtrade Trading Bot Alert</h1>
      <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
      <p>Type: <strong>{webhook_type}</strong></p>
      
      <div class="trade-info">
    """
    
    # Process based on webhook type
    if webhook_type == 'entry':
        # Entry - bot executes a long/short
        body_text += "📈 ENTERING TRADE\n"
        body_text += f"Pair: {webhook_data.get('pair', 'Unknown')}\n"
        body_text += f"Direction: {webhook_data.get('direction', 'Unknown')}\n"
        body_text += f"Order Type: {webhook_data.get('order_type', 'Unknown')}\n"
        body_text += f"Price: {webhook_data.get('open_rate', 'Unknown')}\n"
        body_text += f"Amount: {webhook_data.get('amount', 'Unknown')}\n"
        body_text += f"Stake Amount: {webhook_data.get('stake_amount', 'Unknown')} {webhook_data.get('stake_currency', '')}\n"
        body_text += f"Enter Tag: {webhook_data.get('enter_tag', 'Unknown')}\n"
        
        body_html += f"""
        <h2>📈 ENTERING TRADE</h2>
        <ul>
          <li>Pair: <strong>{webhook_data.get('pair', 'Unknown')}</strong></li>
          <li>Direction: {webhook_data.get('direction', 'Unknown')}</li>
          <li>Order Type: {webhook_data.get('order_type', 'Unknown')}</li>
          <li>Price: {webhook_data.get('open_rate', 'Unknown')}</li>
          <li>Amount: {webhook_data.get('amount', 'Unknown')}</li>
          <li>Stake Amount: {webhook_data.get('stake_amount', 'Unknown')} {webhook_data.get('stake_currency', '')}</li>
          <li>Enter Tag: {webhook_data.get('enter_tag', 'Unknown')}</li>
        </ul>
        """
        
    elif webhook_type == 'entry_cancel':
        # Entry cancel - bot cancels a long/short order
        body_text += "🚫 ENTRY ORDER CANCELLED\n"
        body_text += f"Pair: {webhook_data.get('pair', 'Unknown')}\n"
        body_text += f"Direction: {webhook_data.get('direction', 'Unknown')}\n"
        body_text += f"Order Type: {webhook_data.get('order_type', 'Unknown')}\n"
        body_text += f"Price: {webhook_data.get('limit', 'Unknown')}\n"
        body_text += f"Amount: {webhook_data.get('amount', 'Unknown')}\n"
        body_text += f"Stake Amount: {webhook_data.get('stake_amount', 'Unknown')} {webhook_data.get('stake_currency', '')}\n"
        
        body_html += f"""
        <h2>🚫 ENTRY ORDER CANCELLED</h2>
        <ul>
          <li>Pair: <strong>{webhook_data.get('pair', 'Unknown')}</strong></li>
          <li>Direction: {webhook_data.get('direction', 'Unknown')}</li>
          <li>Order Type: {webhook_data.get('order_type', 'Unknown')}</li>
          <li>Price: {webhook_data.get('limit', 'Unknown')}</li>
          <li>Amount: {webhook_data.get('amount', 'Unknown')}</li>
          <li>Stake Amount: {webhook_data.get('stake_amount', 'Unknown')} {webhook_data.get('stake_currency', '')}</li>
        </ul>
        """
        
    elif webhook_type == 'entry_fill':
        # Entry fill - bot filled a long/short order
        body_text += "✅ ENTRY ORDER FILLED\n"
        body_text += f"Pair: {webhook_data.get('pair', 'Unknown')}\n"
        body_text += f"Direction: {webhook_data.get('direction', 'Unknown')}\n"
        body_text += f"Order Type: {webhook_data.get('order_type', 'Unknown')}\n"
        body_text += f"Fill Price: {webhook_data.get('open_rate', 'Unknown')}\n"
        body_text += f"Amount: {webhook_data.get('amount', 'Unknown')}\n"
        body_text += f"Stake Amount: {webhook_data.get('stake_amount', 'Unknown')} {webhook_data.get('stake_currency', '')}\n"
        body_text += f"Enter Tag: {webhook_data.get('enter_tag', 'Unknown')}\n"
        
        body_html += f"""
        <h2>✅ ENTRY ORDER FILLED</h2>
        <ul>
          <li>Pair: <strong>{webhook_data.get('pair', 'Unknown')}</strong></li>
          <li>Direction: {webhook_data.get('direction', 'Unknown')}</li>
          <li>Order Type: {webhook_data.get('order_type', 'Unknown')}</li>
          <li>Fill Price: {webhook_data.get('open_rate', 'Unknown')}</li>
          <li>Amount: {webhook_data.get('amount', 'Unknown')}</li>
          <li>Stake Amount: {webhook_data.get('stake_amount', 'Unknown')} {webhook_data.get('stake_currency', '')}</li>
          <li>Enter Tag: {webhook_data.get('enter_tag', 'Unknown')}</li>
        </ul>
        """
        
    elif webhook_type == 'exit':
        # Exit - bot exits a trade
        body_text += "📉 EXITING TRADE\n"
        body_text += f"Pair: {webhook_data.get('pair', 'Unknown')}\n"
        body_text += f"Direction: {webhook_data.get('direction', 'Unknown')}\n"
        body_text += f"Order Type: {webhook_data.get('order_type', 'Unknown')}\n"
        body_text += f"Price: {webhook_data.get('limit', 'Unknown')}\n"
        body_text += f"Amount: {webhook_data.get('amount', 'Unknown')}\n"
        body_text += f"Profit: {webhook_data.get('profit_amount', 'Unknown')} {webhook_data.get('stake_currency', '')} ({webhook_data.get('profit_ratio', 'Unknown')})\n"
        body_text += f"Exit Reason: {webhook_data.get('exit_reason', 'Unknown')}\n"
        
        # Format profit ratio as percentage if it's a number
        profit_ratio = webhook_data.get('profit_ratio', 0)
        try:
            profit_ratio = float(profit_ratio) * 100
            profit_ratio_display = f"{profit_ratio:.2f}%"
        except (ValueError, TypeError):
            profit_ratio_display = str(profit_ratio)
        
        body_html += f"""
        <h2>📉 EXITING TRADE</h2>
        <ul>
          <li>Pair: <strong>{webhook_data.get('pair', 'Unknown')}</strong></li>
          <li>Direction: {webhook_data.get('direction', 'Unknown')}</li>
          <li>Order Type: {webhook_data.get('order_type', 'Unknown')}</li>
          <li>Price: {webhook_data.get('limit', 'Unknown')}</li>
          <li>Amount: {webhook_data.get('amount', 'Unknown')}</li>
          <li>Profit: {webhook_data.get('profit_amount', 'Unknown')} {webhook_data.get('stake_currency', '')} ({profit_ratio_display})</li>
          <li>Exit Reason: {webhook_data.get('exit_reason', 'Unknown')}</li>
        </ul>
        """
        
    elif webhook_type == 'exit_fill':
        # Exit fill - bot fills an exit order
        body_text += "✅ EXIT ORDER FILLED\n"
        body_text += f"Pair: {webhook_data.get('pair', 'Unknown')}\n"
        body_text += f"Direction: {webhook_data.get('direction', 'Unknown')}\n"
        body_text += f"Order Type: {webhook_data.get('order_type', 'Unknown')}\n"
        body_text += f"Fill Price: {webhook_data.get('close_rate', 'Unknown')}\n"
        body_text += f"Amount: {webhook_data.get('amount', 'Unknown')}\n"
        body_text += f"Profit: {webhook_data.get('profit_amount', 'Unknown')} {webhook_data.get('stake_currency', '')} ({webhook_data.get('profit_ratio', 'Unknown')})\n"
        body_text += f"Exit Reason: {webhook_data.get('exit_reason', 'Unknown')}\n"
        body_text += f"Trade Duration: {webhook_data.get('open_date', 'Unknown')} to {webhook_data.get('close_date', 'Unknown')}\n"
        
        # Format profit ratio as percentage if it's a number
        profit_ratio = webhook_data.get('profit_ratio', 0)
        try:
            profit_ratio = float(profit_ratio) * 100
            profit_ratio_display = f"{profit_ratio:.2f}%"
            profit_color = "green" if profit_ratio >= 0 else "red"
        except (ValueError, TypeError):
            profit_ratio_display = str(profit_ratio)
            profit_color = "black"
        
        body_html += f"""
        <h2>✅ EXIT ORDER FILLED</h2>
        <ul>
          <li>Pair: <strong>{webhook_data.get('pair', 'Unknown')}</strong></li>
          <li>Direction: {webhook_data.get('direction', 'Unknown')}</li>
          <li>Order Type: {webhook_data.get('order_type', 'Unknown')}</li>
          <li>Fill Price: {webhook_data.get('close_rate', 'Unknown')}</li>
          <li>Amount: {webhook_data.get('amount', 'Unknown')}</li>
          <li>Profit: <span style="color: {profit_color}">{webhook_data.get('profit_amount', 'Unknown')} {webhook_data.get('stake_currency', '')} ({profit_ratio_display})</span></li>
          <li>Exit Reason: {webhook_data.get('exit_reason', 'Unknown')}</li>
          <li>Trade Duration: {webhook_data.get('open_date', 'Unknown')} to {webhook_data.get('close_date', 'Unknown')}</li>
        </ul>
        """
        
    elif webhook_type == 'exit_cancel':
        # Exit cancel - bot cancels an exit order
        body_text += "🚫 EXIT ORDER CANCELLED\n"
        body_text += f"Pair: {webhook_data.get('pair', 'Unknown')}\n"
        body_text += f"Direction: {webhook_data.get('direction', 'Unknown')}\n"
        body_text += f"Order Type: {webhook_data.get('order_type', 'Unknown')}\n"
        body_text += f"Price: {webhook_data.get('limit', 'Unknown')}\n"
        body_text += f"Amount: {webhook_data.get('amount', 'Unknown')}\n"
        body_text += f"Profit: {webhook_data.get('profit_amount', 'Unknown')} {webhook_data.get('stake_currency', '')} ({webhook_data.get('profit_ratio', 'Unknown')})\n"
        
        body_html += f"""
        <h2>🚫 EXIT ORDER CANCELLED</h2>
        <ul>
          <li>Pair: <strong>{webhook_data.get('pair', 'Unknown')}</strong></li>
          <li>Direction: {webhook_data.get('direction', 'Unknown')}</li>
          <li>Order Type: {webhook_data.get('order_type', 'Unknown')}</li>
          <li>Price: {webhook_data.get('limit', 'Unknown')}</li>
          <li>Amount: {webhook_data.get('amount', 'Unknown')}</li>
          <li>Profit: {webhook_data.get('profit_amount', 'Unknown')} {webhook_data.get('stake_currency', '')} ({webhook_data.get('profit_ratio', 'Unknown')})</li>
        </ul>
        """
    
    elif webhook_type == 'strategy_msg':
        # Handle custom message from strategy
        msg = webhook_data.get('msg', 'No message content')
        body_text += "📊 STRATEGY MESSAGE\n"
        
        # Check if message is a dictionary or JSON string
        if isinstance(msg, dict):
            for key, value in msg.items():
                body_text += f"{key}: {value}\n"
            
            body_html += f"""
            <h2>📊 STRATEGY MESSAGE</h2>
            <ul>
            """
            
            for key, value in msg.items():
                body_html += f"<li>{key}: <strong>{value}</strong></li>\n"
            
            body_html += "</ul>"
        else:
            # Try to parse as JSON if it's a string
            try:
                if isinstance(msg, str) and (msg.startswith('{') or msg.startswith('[')):
                    msg_data = json.loads(msg)
                    
                    # If it's a dictionary
                    if isinstance(msg_data, dict):
                        for key, value in msg_data.items():
                            body_text += f"{key}: {value}\n"
                        
                        body_html += f"""
                        <h2>📊 STRATEGY MESSAGE</h2>
                        <ul>
                        """
                        
                        for key, value in msg_data.items():
                            body_html += f"<li>{key}: <strong>{value}</strong></li>\n"
                        
                        body_html += "</ul>"
                    else:
                        # It's probably a list or some other JSON structure
                        body_text += f"Message: {msg}\n"
                        body_html += f"""
                        <h2>📊 STRATEGY MESSAGE</h2>
                        <pre>{json.dumps(msg_data, indent=2)}</pre>
                        """
                else:
                    # Plain text message
                    body_text += f"Message: {msg}\n"
                    body_html += f"""
                    <h2>📊 STRATEGY MESSAGE</h2>
                    <p>{msg}</p>
                    """
            except json.JSONDecodeError:
                # Handle plain text message
                body_text += f"Message: {msg}\n"
                body_html += f"""
                <h2>📊 STRATEGY MESSAGE</h2>
                <p>{msg}</p>
                """
    
    elif webhook_type == 'status':
        # Status - regular status messages
        body_text += f"STATUS UPDATE: {webhook_data.get('status', 'Unknown')}\n"
        
        body_html += f"""
        <h2>STATUS UPDATE</h2>
        <p>Status: <strong>{webhook_data.get('status', 'Unknown')}</strong></p>
        """
    
    else:
        # Unknown webhook type - generic processing
        body_text += f"RECEIVED WEBHOOK: {webhook_type}\n"
        
        # Add all available fields
        for key, value in webhook_data.items():
            if key != 'type':
                body_text += f"{key}: {value}\n"
        
        body_html += f"""
        <h2>RECEIVED WEBHOOK: {webhook_type}</h2>
        <ul>
        """
        
        for key, value in webhook_data.items():
            if key != 'type':
                body_html += f"<li>{key}: {value}</li>\n"
        
        body_html += "</ul>"
    
    # Add complete webhook data to all message types
    body_text += "\nComplete Webhook Data:\n"
    body_text += json.dumps(webhook_data, indent=2)
    
    body_html += """
      </div>
      
      <div class="data-section">
        <h3>Complete Webhook Data</h3>
        <pre>
    """
    body_html += json.dumps(webhook_data, indent=2)
    body_html += """
        </pre>
      </div>
    </body>
    </html>
    """
    
    try:
        # Send email using AWS SES
        response = ses_client.send_email(
            Source=EMAIL_SENDER,
            Destination={
                'ToAddresses': [
                    EMAIL_RECIPIENT,
                ],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        logger.info(f"Email sent for webhook type {webhook_type}! Message ID: {response['MessageId']}")
        
        return {
            'status': 'success',
            'message': f'Webhook received and email sent for {webhook_type}',
            'messageId': response['MessageId']
        }
    except Exception as e:
        logger.error(f"Failed to send email for webhook type {webhook_type}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/webhook")
async def webhook(request: Request, token: Optional[str] = None, authorized: bool = Depends(verify_api_key)):
    """
    Webhook endpoint with query parameter authentication
    """
    try:
        # Get the webhook data
        webhook_data = await request.json()
        # Process webhook data and send email
        return await process_webhook_data(webhook_data)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Log-only webhook endpoints - moved before path-based authentication to avoid conflicts
@app.post("/webhook/log-only")
async def webhook_log_only(request: Request, token: Optional[str] = None, authorized: bool = Depends(verify_api_key)):
    """
    Webhook endpoint that only logs the data without sending emails or other processing.
    Useful for debugging or when you only want to record trading signals.
    """
    try:
        # Get the webhook data
        webhook_data = await request.json()
        
        # Validate input data
        if not isinstance(webhook_data, dict):
            raise HTTPException(status_code=400, detail="Invalid webhook data format")
        
        # Log the received webhook with special tag for easy filtering
        logger.info(f"LOG_ONLY_WEBHOOK: {json.dumps(webhook_data, indent=2)}")
        
        # Return success response
        return {
            'status': 'success',
            'message': 'Webhook received and logged (no email sent)',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing log-only webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/log-only/{path_key}")
async def webhook_log_only_path_auth(path_key: str, request: Request):
    """
    Path-based authentication version of the log-only webhook endpoint
    """
    # Verify the path key
    if not API_KEY or path_key != API_KEY:
        logger.warning(f"Invalid API key attempt with path key: {path_key}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key in path",
        )
    
    try:
        # Get the webhook data
        webhook_data = await request.json()
        
        # Validate input data
        if not isinstance(webhook_data, dict):
            raise HTTPException(status_code=400, detail="Invalid webhook data format")
        
        # Log the received webhook with special tag for easy filtering
        logger.info(f"LOG_ONLY_WEBHOOK: {json.dumps(webhook_data, indent=2)}")
        
        # Return success response
        return {
            'status': 'success',
            'message': 'Webhook received and logged (no email sent)',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing log-only webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Path-based authentication - now comes AFTER specific routes to avoid conflicts
@app.post("/webhook/{path_key}")
async def webhook_path_auth(
    path_key: str, 
    request: Request,
    # Exclude "log-only" from path parameters to avoid conflicts
):
    """
    Webhook endpoint with path-based authentication
    """
    # Check if the path_key is "log-only" - should not get here due to routing order, but just in case
    if path_key == "log-only":
        raise HTTPException(
            status_code=404,
            detail="Invalid endpoint - use /webhook/log-only for log-only requests",
        )
    
    # Verify the path key
    if not API_KEY or path_key != API_KEY:
        logger.warning(f"Invalid API key attempt with path key: {path_key}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key in path",
        )
    
    try:
        # Get the webhook data
        webhook_data = await request.json()
        # Process webhook data and send email
        return await process_webhook_data(webhook_data)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Add an index route for easy health check
@app.get("/")
async def index():
    logger.debug("Health check endpoint accessed")
    return {"status": "online", "service": "Freqtrade Email Notifier"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting server on 127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)