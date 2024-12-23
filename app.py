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
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid = os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"
client = Client(account_sid, auth_token)
sent_texts = set()
x=0

def get_send_time(secs):
    wait_secs=secs
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15, seconds = wait_secs)
    print(wait_secs)
    return send_at.isoformat()

def send_text(text_nbr, message, secs):
    delayed_send = secs
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        try:
            message = client.messages.create(
                body=message,
                from_=twilio_number,
                to=text_nbr,
                messaging_service_sid=messaging_sid,
                send_at=get_send_time(delayed_send),
                schedule_type="fixed"
            )
            sent_texts.add(text_nbr)
            return True
        except Exception as e:
            print(f"Error sending SMS to {text_nbr}: {e}")
            return False
    return False

def process_data(data_path):
    df = pd.read_csv(data_path)
    df_filtered = df[df['Age'] > 17]
    df_filtered = df_filtered[['First_Name', 'Last_Name', 'Phone Number']]
    df_filtered = df_filtered.dropna(subset=['Phone Number'])
    df_filtered['is_valid_phone'] = df_filtered['Phone Number'].apply(lambda x: is_valid_phone_number(x))
    df_filtered = df_filtered[df_filtered['is_valid_phone']]

    df_filtered = df_filtered.drop_duplicates(subset=['Phone Number']) 

    data_list = df_filtered.to_dict('records')
    return data_list
    
def is_valid_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number, region="US")
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False

def sms_send(msg_in, data_list):
    success_count = 1
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for data in data_list:
            msg = f"Hello {data['First_Name']},\n"
            msg += msg_in + "\n"
            print(success_count, ". ", data['Last_Name'], "-", data['Phone Number'])
            future = executor.submit(send_text, data['Phone Number'], msg, success_count)
            futures.append(future)
            success_count += 1

        for future in futures:
            result = future.result()

    return
 
@app.route("/sms", methods=['POST'])        
def incoming_sms():
    message_body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    first_word = message_body.split()[0].lower()
    msg_in = message_body.strip()
    lines = msg_in.splitlines()

    if len(lines) > 1:
        msg_in = "\n".join(lines[1:])
        
    if first_word == "sms77216" and from_number == '+15099902828':
   
        data_list = process_data("Westmond_Master.csv")
        num_messages_sent = sms_send(msg_in, data_list)
    
        client.messages.create(
            body=f'Message scheduled to {num_messages_sent} individuals.',
            from_=twilio_number,
            to=from_number
        )
        return f"Successfully sent SMS to {num_messages_sent} recipients."
        
    elif first_word == "min77216":
        subprocess.run(["python", "SMS_Ministers.py", msg_in, from_number])

    elif first_word == "cancel-sms":
        messages = client.messages.list(limit=300)  # Adjust limit as needed
        canceled_count = 0 
        for message in messages:
            if message.status == 'scheduled':
                try:
                    client.messages(message.sid).update(status='canceled')
                    canceled_count += 1
                except Exception as e:
                    print(f"Error canceling message {message.sid}: {e}") 
    
        client.messages.create(
            body=f'{canceled_count} Messages canceled',
            from_='+12086034040',
            to=from_number
        )
        return canceled_count 
        
    elif first_word == "ecs77216" and (from_number == '+15099902828' or from_number == '+13607428998'):
        subprocess.run(["python", "SMS_Send.py", msg_in, from_number])

    else:
        client.messages.create(
            body='From: ' + from_number + '\n' + msg_in,
            from_=twilio_number,
            to='+15099902828'
        )
    return

if __name__ == "__main__":
    app.run()
