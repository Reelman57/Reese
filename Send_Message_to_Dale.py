import os
from flask import Flask, request
from twilio.rest import Client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = "+12086034040"
client = Client(account_sid, auth_token)

client.messages.create(
    body="Test of subprocess",
    from_=twilio_number,
    to="+12086034040"
)
