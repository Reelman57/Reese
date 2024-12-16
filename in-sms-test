from flask import Flask, request
from twilio.rest import Client

# Load credentials from environment variables
account_sid = "ACe5192182f6433969f03acfbfabeca240"
auth_token  = "998e399acf35b27c418467e3c6672a4e"
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
    app.run(debug=True)
