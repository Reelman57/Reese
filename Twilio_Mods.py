from itertools import count
import pandas as pd
import subprocess
import numpy as np
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import time
import pytz
import re
import sys

def twilio_creds():
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    messaging_sid= os.environ['TWILIO_MSGNG_SID']
    twilio_number = "+12086034040"
    client = Client(account_sid, auth_token)

def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15)
    return send_at

def send_text(text_nbr, message, sent_texts=set(), Client=None):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        send_at = get_send_time()
        message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=text_nbr,
            messaging_service_sid=messaging_sid,
            send_at=send_at.isoformat(),
            schedule_type="fixed"
        )

def send_voice(to_number, message, sent_voice=set(), Client=None):
    if to_number not in sent_voice and not pd.isna(to_number):
        call = client.calls.create(
            twiml = "<Response><Pause length=\"3\"/><Say voice=\"Google.en-US-Standard-J\">" + message + "Goodbye. </Say></Response>",
            to=to_number,
            from_=twilio_number
        )

def send_email(to_addr, subject, body, sent_email=set()):
    if to_addr not in sent_email and not pd.isna(to_addr):

        if isinstance(to_addr, str):
            msg = MIMEMultipart()
            msg['From'] = 'eqp77216@gmail.com'
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:  
                smtp.starttls()
                smtp.login('eqp77216@gmail.com', 'ogla wwsg mnqw nmhn') 
                smtp.sendmail(msg['From'], msg['To'], msg.as_string())

def get_data():
    data_path = "Westmond_Master.csv"

    df = pd.read_csv(data_path)
    df_filtered = df[(df['Age'] > 17)]
    df_sorted = df_filtered.sort_values(by='Last_Name', ascending=True)
    
    with open('DO_NOT_SEND.txt', 'r') as file:
        sent_texts = set(line.strip() for line in file)
    
