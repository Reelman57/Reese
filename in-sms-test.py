import os
from flask import Flask, request
from twilio.rest import Client

# Load credentials from environment variables
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = "+12086034040"

client = None  # Initialize later

try:
  # Check if credentials are available
  if not account_sid or not auth_token:
    raise ValueError("Missing environment variables for Twilio credentials")

  # Initialize client with credentials
  client = Client(account_sid, auth_token)
except ValueError as e:
  print(f"Error: {e}")

app = Flask(__name__)

@app.route("/sms", methods=['POST'])
def incoming_sms():
  if not client:
    return "Error: Twilio client not initialized", 500

  message_body = request.values.get('Body', None)
  from_number = request.values.get('From', None)

  try:
    # Send SMS using Twilio client
    client.messages.create(
      body="Hello Back!",
      from_=twilio_number,
      to=from_number
    )
    return "SMS Sent Successfully", 200
  except Exception as e:
    print(f"Error sending SMS: {e}")
    return "Error: Failed to send SMS", 500

if __name__ == "__main__":
  app.run(debug=True)
    
