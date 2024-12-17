import os
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)

# Your Account SID and Auth Token from twilio.com/console
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = "+12086034040"  # Can be either single or double quotes

client = Client(account_sid, auth_token)

@app.route("/sms", methods=['POST'])
def handle_sms():
    message = request.get_json()  # Access message data from request body
    body = message.get('body', '').strip()  # Extract body from message
    first_word = body.split()[0].lower()

    if first_word == "help":
        handle_help_request(message)
    elif first_word == "order":
        handle_order_request(message)
    else:
        handle_default_response(message)

def handle_help_request(message):
    # Implement logic for handling help requests
    response = client.messages.create(
        body="You can use 'help' for assistance or 'order' to place an order.",
        from_=twilio_number,
        to=message.get('from')  # Access sender number from message
    )

def handle_order_request(message):
    # Implement logic for handling order requests
    response = client.messages.create(
        body="Thank you for your order! We'll process it shortly.",
        from_=twilio_number,
        to=message.get('from')
    )

def handle_default_response(message):
    # Implement logic for handling default responses
    response = client.messages.create(
        body="Sorry, I didn't understand. Please try again.",
        from_=twilio_number,
        to=message.get('from')
    )

@app.route("/healthcheck", methods=['GET'])
def healthcheck():
    return '{"status":"ok"}'

if __name__ == "__main__":
    app.run()
