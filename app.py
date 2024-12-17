iimport os
from flask import Flask, request
from twilio.rest import Client

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

    if first_word == "dale":
        client.messages.create(
        body=first_word,
        from_=twilio_number,
        to=from_number
        )
    elif first_word == "trudy":
       
    else:
    
if __name__ == "__main__":
    app.run()
