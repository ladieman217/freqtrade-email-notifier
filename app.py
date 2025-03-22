from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import boto3
import json
import os
import uvicorn
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Freqtrade Webhook Notifier")

# Configuration
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'your-sender@example.com')
EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', 'your-recipient@example.com')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
API_KEY = os.environ.get('API_KEY', '')

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

@app.post("/webhook")
async def webhook(request: Request, token: Optional[str] = None, authorized: bool = Depends(verify_api_key)):
    try:
        # Get the webhook data
        webhook_data = await request.json()
        
        # Validate input data
        if not isinstance(webhook_data, dict):
            raise HTTPException(status_code=400, detail="Invalid webhook data format")
        
        # Ensure 'type' field exists
        if 'type' not in webhook_data:
            raise HTTPException(status_code=400, detail="Missing 'type' field in webhook data")
        
        # Log the received webhook
        print(f"Received webhook: {json.dumps(webhook_data, indent=2)}")
        
        # Prepare email content
        subject = f"Freqtrade Alert - {webhook_data.get('type', 'Unknown')}"
        
        # Format the email body
        body_text = "Freqtrade Trading Bot Alert\n\n"
        body_text += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body_text += f"Type: {webhook_data.get('type', 'Unknown')}\n\n"
        
        # Add trade details if available
        if 'exchange' in webhook_data:
            body_text += f"Exchange: {webhook_data.get('exchange')}\n"
        if 'pair' in webhook_data:
            body_text += f"Trading Pair: {webhook_data.get('pair')}\n"
        if 'order_type' in webhook_data:
            body_text += f"Order Type: {webhook_data.get('order_type')}\n"
        if 'side' in webhook_data:
            body_text += f"Side: {webhook_data.get('side')}\n"
        if 'price' in webhook_data:
            body_text += f"Price: {webhook_data.get('price')}\n"
        if 'amount' in webhook_data:
            body_text += f"Amount: {webhook_data.get('amount')}\n"
        if 'trade_id' in webhook_data:
            body_text += f"Trade ID: {webhook_data.get('trade_id')}\n"
        
        # Add all other data from webhook
        body_text += "\nComplete Webhook Data:\n"
        body_text += json.dumps(webhook_data, indent=2)
        
        # Create HTML version
        body_html = f"""
        <html>
        <head></head>
        <body>
          <h1>Freqtrade Trading Bot Alert</h1>
          <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
          <p>Type: {webhook_data.get('type', 'Unknown')}</p>
          
          <h2>Details</h2>
          <ul>
        """
        
        # Add trade details if available
        if 'exchange' in webhook_data:
            body_html += f"<li>Exchange: {webhook_data.get('exchange')}</li>\n"
        if 'pair' in webhook_data:
            body_html += f"<li>Trading Pair: {webhook_data.get('pair')}</li>\n"
        if 'order_type' in webhook_data:
            body_html += f"<li>Order Type: {webhook_data.get('order_type')}</li>\n"
        if 'side' in webhook_data:
            body_html += f"<li>Side: {webhook_data.get('side')}</li>\n"
        if 'price' in webhook_data:
            body_html += f"<li>Price: {webhook_data.get('price')}</li>\n"
        if 'amount' in webhook_data:
            body_html += f"<li>Amount: {webhook_data.get('amount')}</li>\n"
        if 'trade_id' in webhook_data:
            body_html += f"<li>Trade ID: {webhook_data.get('trade_id')}</li>\n"
        
        body_html += """
          </ul>
          
          <h2>Complete Webhook Data</h2>
          <pre>
        """
        body_html += json.dumps(webhook_data, indent=2)
        body_html += """
          </pre>
        </body>
        </html>
        """
        
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
        
        print(f"Email sent! Message ID: {response['MessageId']}")
        
        # Return success response
        return {
            'status': 'success',
            'message': 'Webhook received and email sent',
            'messageId': response['MessageId']
        }
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a path-based endpoint for authentication
@app.post("/webhook/{path_key}")
async def webhook_path_auth(path_key: str, request: Request):
    """
    Webhook endpoint with path-based authentication
    """
    # Verify the path key
    if not API_KEY or path_key != API_KEY:
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
        
        # Ensure 'type' field exists
        if 'type' not in webhook_data:
            raise HTTPException(status_code=400, detail="Missing 'type' field in webhook data")
        
        # Log the received webhook
        print(f"Received webhook: {json.dumps(webhook_data, indent=2)}")
        
        # Prepare email content
        subject = f"Freqtrade Alert - {webhook_data.get('type', 'Unknown')}"
        
        # Format the email body
        body_text = "Freqtrade Trading Bot Alert\n\n"
        body_text += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body_text += f"Type: {webhook_data.get('type', 'Unknown')}\n\n"
        
        # Add trade details if available
        if 'exchange' in webhook_data:
            body_text += f"Exchange: {webhook_data.get('exchange')}\n"
        if 'pair' in webhook_data:
            body_text += f"Trading Pair: {webhook_data.get('pair')}\n"
        if 'order_type' in webhook_data:
            body_text += f"Order Type: {webhook_data.get('order_type')}\n"
        if 'side' in webhook_data:
            body_text += f"Side: {webhook_data.get('side')}\n"
        if 'price' in webhook_data:
            body_text += f"Price: {webhook_data.get('price')}\n"
        if 'amount' in webhook_data:
            body_text += f"Amount: {webhook_data.get('amount')}\n"
        if 'trade_id' in webhook_data:
            body_text += f"Trade ID: {webhook_data.get('trade_id')}\n"
        
        # Add all other data from webhook
        body_text += "\nComplete Webhook Data:\n"
        body_text += json.dumps(webhook_data, indent=2)
        
        # Create HTML version
        body_html = f"""
        <html>
        <head></head>
        <body>
          <h1>Freqtrade Trading Bot Alert</h1>
          <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
          <p>Type: {webhook_data.get('type', 'Unknown')}</p>
          
          <h2>Details</h2>
          <ul>
        """
        
        # Add trade details if available
        if 'exchange' in webhook_data:
            body_html += f"<li>Exchange: {webhook_data.get('exchange')}</li>\n"
        if 'pair' in webhook_data:
            body_html += f"<li>Trading Pair: {webhook_data.get('pair')}</li>\n"
        if 'order_type' in webhook_data:
            body_html += f"<li>Order Type: {webhook_data.get('order_type')}</li>\n"
        if 'side' in webhook_data:
            body_html += f"<li>Side: {webhook_data.get('side')}</li>\n"
        if 'price' in webhook_data:
            body_html += f"<li>Price: {webhook_data.get('price')}</li>\n"
        if 'amount' in webhook_data:
            body_html += f"<li>Amount: {webhook_data.get('amount')}</li>\n"
        if 'trade_id' in webhook_data:
            body_html += f"<li>Trade ID: {webhook_data.get('trade_id')}</li>\n"
        
        body_html += """
          </ul>
          
          <h2>Complete Webhook Data</h2>
          <pre>
        """
        body_html += json.dumps(webhook_data, indent=2)
        body_html += """
          </pre>
        </body>
        </html>
        """
        
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
        
        print(f"Email sent! Message ID: {response['MessageId']}")
        
        # Return success response
        return {
            'status': 'success',
            'message': 'Webhook received and email sent',
            'messageId': response['MessageId']
        }
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add an index route for easy health check
@app.get("/")
async def index():
    return {"status": "online", "service": "Freqtrade Webhook Email Notifier"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    uvicorn.run(app, host="0.0.0.0", port=port) 