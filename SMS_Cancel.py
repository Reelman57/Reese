from twilio.rest import Client
import os
import time

# LIVE Credentials
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid= os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"
client = Client(account_sid, auth_token)

# Function to cancel all scheduled messages
def cancel_all_scheduled_messages():
    # Retrieve all messages (you might want to filter by date or status)
    messages = client.messages.list(limit=300)  # Adjust limit as needed

    for message in messages:
        if message.status == 'scheduled':  # Check if the message is scheduled
            client.messages(message.sid).update(status='canceled')
            print(f"Canceled message SID: {message.sid}")

# Call the function
cancel_all_scheduled_messages()
