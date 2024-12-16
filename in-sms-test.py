import os
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)

# Load your Twilio credentials from environment variables
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = "+12086034040" 

client = Client(account_sid, auth_token)

@app.route("/sms", methods=['POST'])
def incoming_sms():
    message_body = request.values.get('Body', None)
    from_number = request.values.get('From', None)

    message = client.messages.create(
        body="Hello!",
        from_=twilio_number,
        to=from_number
    )

