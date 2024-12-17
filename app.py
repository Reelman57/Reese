import os
from flask import Flask, request, make_response
from twilio.rest import Client
import subprocess

app = Flask(__name__)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = "+12086034040"
client = Client(account_sid, auth_token)

@app.route("/sms", methods=['POST'])

def incoming_sms():
    message_body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    first_word = message_body.split()[0].lower()

    msg = message_body.strip()
    lines = msg.splitlines()

    if len(lines) > 1:
        msg = "\n".join(lines[1:])

    if first_word == "dale":
        client.messages.create(
        body=msg,
        from_=twilio_number,
        to=from_number
        )
    elif first_word == "ecs77216" and from_number == '+15099902828':
        
        subprocess.run(["python", "ECS_Send.py",msg,from_number])
       
    # else:
    
if __name__ == "__main__":
    app.run()
