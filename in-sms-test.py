import os
from flask import Flask, request
from twilio.rest import Client

# Load credentials from environment variables
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = "+12086034040"

client = Client(account_sid, auth_token)

app = Flask(__name__)

@app.route("/sms", methods=['POST'])
def incoming_sms():
    message_body = request.values.get('Body', None)
    from_number = request.values.get('From', None)

    client.messages.create(
        body="Hello Back!",
        from_=twilio_number,
        to=from_number
    )

    if __name__ == "__main__":
    
