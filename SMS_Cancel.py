from twilio.rest import Client
import os
import time

# Load credentials from environment variables
account_sid = "ACe5192182f6433969f03acfbfabeca240"
auth_token  = "998e399acf35b27c418467e3c6672a4e"

client = Client(account_sid, auth_token)

# Function to cancel all scheduled messages
def cancel_all_scheduled_messages():
    # Retrieve all messages (you might want to filter by date or status)
    messages = client.messages.list(limit=20)  # Adjust limit as needed

    for message in messages:
        if message.status == 'scheduled':  # Check if the message is scheduled
            client.messages(message.sid).update(status='canceled')
            print(f"Canceled message SID: {message.sid}")

# Call the function
cancel_all_scheduled_messages()