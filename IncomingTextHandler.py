import os
from twilio.rest import Client
from flask import Flask, request

# Load credentials from environment variables
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = "+12086034040"

client = Client(account_sid, auth_token)

app = Flask(__name__)

def handle_sms(message_body):
    first_word = message_body.split()[0]

    match first_word:
        case "help":
            print("Help request received")
        case "status":
            print("Status request received")
        case "Hello":
            client.messages.create(
                body=f"From: {message.from_}\nMessage: {message_body}",
                from_= twilio_number ,
                to="+15099902828"
            )
        case _:
            client.messages.create(
                body=f"From: {message.from_}\nMessage: {message_body}",
                from_= twilio_number ,
                to="+15099902828"
            )

@app.route("/sms", methods=['POST'])
def incoming_sms():
    message_body = request.values.get('Body', None)

    handle_sms(message_body)

if __name__ == "__main__":
