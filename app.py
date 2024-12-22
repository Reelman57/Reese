from flask import Flask, request, make_response
from twilio.rest import Client
import subprocess
import pandas as pd
import os
from datetime import datetime, timedelta
from twilio.rest import Client
import pytz
import re
import sys
import phonenumbers

app = Flask(__name__)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid = os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"
Client = Client(account_sid, auth_token)

@app.route("/sms", methods=['POST'])

def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15)
    return send_at.isoformat()

def send_text(text_nbr, message):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        try:
            message = Client.messages.create(
                body=message,
                from_=twilio_number,
                to=text_nbr,
                messaging_service_sid=messaging_sid,
                send_at=get_send_time(),
                schedule_type="fixed"
            )
            sent_texts.add(text_nbr)
            return message  # Return the message object
        except Exception as e:
            # Log the error (consider using a logging library)
            print(f"Error sending SMS to {text_nbr}: {e}")
            return None  # Return None to indicate failure
    else:
        return None

def process_data(data_path):
    df = pd.read_csv(data_path)
    df_filtered = df[df['Age'] > 17]
    df_filtered = df_filtered[['First_Name', 'Last_Name', 'Phone Number']]
    df_filtered = df_filtered.dropna(subset=['Phone Number'])
    df_filtered['is_valid_phone'] = df_filtered['Phone Number'].apply(lambda x: is_valid_phone_number(x))
    df_filtered = df_filtered[df_filtered['is_valid_phone']]

    return df_filtered

def is_valid_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number, region="US")
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False
        
def incoming_sms():
    message_body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    first_word = message_body.split()[0].lower()

    msg_in = message_body.strip()
    lines = msg_in.splitlines()
    sent_texts = set()

    if len(lines) > 1:
        msg_in = "\n".join(lines[1:])

    # with open('DO_NOT_SEND.txt', 'r') as file:
    #     sent_texts = set(line.strip() for line in file)
    x = 0

    # ----------------------------------------------------------------
    if first_word == "sms77216" and from_number == '+15099902828':
        data_path = "Westmond_Master.csv"
        df_filtered = process_data(data_path)

        for index, row in df_filtered.iterrows():
            msg = f"Hello {row['First_Name']},\n"
            msg += msg_in + "\n"

            if not pd.isna(row['Phone Number']):
                # send_text(row['Phone Number'], msg)
                x += 1

            Client.messages.create(
                body=f'Message sent to {x} individuals.',
                from_=twilio_number,
                to=from_number
            )
    # ----------------------------------------------------------------
    elif first_word == "min77216":
        subprocess.run(["python", "SMS_Ministers.py", msg, from_number])

    elif first_word == "cancel-sms":
        subprocess.run(["python", "SMS_Cancel.py", msg, from_number])

    elif first_word == "ecs77216" and (from_number == '+15099902828' or from_number == '+13607428998'):
        subprocess.run(["python", "SMS_Send.py", msg, from_number])

    else:
        Client.messages.create(
            body='From: ' + from_number + '\n' + msg,
            from_=twilio_number,
            to='+15099902828'
        )

if __name__ == "__main__":
    app.run()
