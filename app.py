from itertools import count
from flask import Flask, request, make_response
from twilio.rest import Client
import subprocess
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
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
sent_voice = set()
with open('DO_NOT_SEND.txt', 'r') as file:
    sent_texts = set(line.strip() for line in file)
x=0
# --------------------------------------------------------------------------
def get_send_time():
    global x
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15, seconds = x)
    x+=1
    return send_at.isoformat()
# --------------------------------------------------------------------------
def send_text(text_nbr, message, now):
    global sent_texts
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        try:
            message = client.messages.create(
                body=message,
                from_=twilio_number,
                to=text_nbr,
                messaging_service_sid=messaging_sid,
                if now != True
                    send_at=get_send_time(),
                    schedule_type="fixed"
            )
            sent_texts.add(text_nbr)
            return True
        except Exception as e:
            print(f"Error sending SMS to {text_nbr}: {e}")
            return False
    return False
# --------------------------------------------------------------------------
def send_voice(msg_in, data_list):
    sent_voice = set()
    calls = []
    for data in data_list:
        to_number = data.get('Phone Number')
        if to_number not in sent_voice and not pd.isna(to_number):
            try:
                msg = f"Hello {data['First_Name']},\n" + msg_in + "\n"
                call = client.calls.create(
                    twiml=f"<Response><Pause length=\"3\"/><Say voice=\"Google.en-US-Standard-J\">{msg} Goodbye. </Say></Response>",
                    to=to_number,
                    from_=twilio_number
                )
                sent_voice.add(to_number)
                calls.append(call)
                print("Voice - ", data['Last_Name'], "-", data['Phone Number']) 
            except Exception as e:
                print(f"Error sending voice call to {to_number}: {e}")
    return calls 
# --------------------------------------------------------------------------        
def send_email(subject, body, data_list):
    sent_emails = set()
    for data in data_list:
        email = data.get('Email')
        message = f"Hello {data['First_Name']},\n"
        message += body + "\n"
        if email and not pd.isna(email):
            try:
                msg = MIMEMultipart()
                msg['From'] = os.environ.get('EMAIL_ADDRESS')
                msg['To'] = email
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))

                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(os.environ.get('EMAIL_ADDRESS'), os.environ.get('EMAIL_PASSWORD'))
                    smtp.sendmail(msg['From'], msg['To'], msg.as_string())
                    sent_emails.add(email)
                print("Email - ", data['Last_Name'], "-", email) 
            except Exception as e:
                print(f"Error sending email to {email}: {e}")
        else:
            print(f"Invalid or missing email address for {data}")
    return len(sent_emails)
# --------------------------------------------------------------------------
def process_data(data_path):
    df = pd.read_csv(data_path)
    df_filtered = df[df['Age'] > 17]
    df_filtered = df_filtered[['First_Name', 'Last_Name', 'Phone Number', 'Email']]
    df_filtered = df_filtered.dropna(subset=['Phone Number'])
    df_filtered['is_valid_phone'] = df_filtered['Phone Number'].apply(lambda x: is_valid_phone_number(x))
    df_filtered = df_filtered[df_filtered['is_valid_phone']]

    df_filtered = df_filtered.drop_duplicates(subset=['Phone Number']) 

    data_list = df_filtered.to_dict('records')
    return data_list
# --------------------------------------------------------------------------    
def is_valid_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number, region="US")
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False
# --------------------------------------------------------------------------
def sms_send(from_number, msg_in, data_list, now):
    success_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for data in data_list:
            msg = f"Hello {data['First_Name']},\n"
            msg += msg_in + "\n"
            future = executor.submit(send_text, data['Phone Number'], msg, now)
            futures.append(future)
            success_count += 1
            print("SMS - ", data['Last_Name'], "-", data['Phone Number'])

        for future in futures:
            try:
                result = future.result() 
            except Exception as e:
                app.logger.error(f"Error processing future: {e}")
                
    client.messages.create(
        body=f'Message scheduled to {success_count} individuals.',
        from_=twilio_number,
        to=from_number
    )       
    return success_count
# -------------------------------------------------------------------------- 
@app.route("/sms", methods=['POST'])        
def incoming_sms():
    message_body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    data_list = process_data("Westmond_Master_Test.csv")

    if message_body is None or from_number is None:
        return "Invalid request: Missing message body or sender number", 400

    first_word = message_body.split()[0].lower()
    msg_in = message_body.strip()
    lines = msg_in.splitlines()

    if len(lines) > 1:
        msg_in = "\n".join(lines[1:])
# --------------------------------------------------------------------------
    if first_word == "sms77216" and from_number == '+15099902828':
        try:
            num_messages_sent = sms_send(msg_in, data_list)
            return num_messages_sent 
        except Exception as e:
            return f"An error occurred: {str(e)}", 500
# --------------------------------------------------------------------------       
    elif first_word == "min77216":
        subprocess.run(["python", "SMS_Ministers.py", msg_in, from_number])
# --------------------------------------------------------------------------
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
# --------------------------------------------------------------------------        
    elif first_word == "ecs77216" and (from_number == '+15099902828' or from_number == '+13607428998'):
        subject = "Emergency Communications System"
        now=True
        sms_send(from_number, msg_in, data_list, now)
        send_email(subject, msg_in, data_list) 
        send_voice(msg_in, data_list)
        now=""
    return
# --------------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
