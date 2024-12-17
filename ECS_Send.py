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

# LIVE Credentials
account_sid = "ACe5192182f6433969f03acfbfabeca240"
messaging_sid = 'MGfa2a91d90fbd477cfa5a2de48d05b2be'
auth_token  = "998e399acf35b27c418467e3c6672a4e"

client = Client(account_sid, auth_token)

def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=5)
    return send_at

def send_texts(text_nbr, message):

    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        # send_at = get_send_time()
        message = client.messages.create(
        body = message,
        from_='+12086034040',
        to = text_nbr
        )
        # messaging_service_sid = messaging_sid,
        # send_at=send_at.isoformat(),
        # schedule_type="fixed"
        # )
        sent_texts.add(row["Phone Number"])


def send_voice(to_number, message):

    if to_number not in sent_voice and not pd.isna(to_number):

        call = client.calls.create(
            twiml = "<Response><Pause length=\"3\"/><Say voice=\"Google.en-US-Standard-J\">" + message + "Goodbye. </Say></Response>",
            to=to_number,
            from_="+12086034040"
        )

        sent_voice.add(row["Phone Number"])

def send_email(to_addr, subject, body):

    if to_addr not in sent_email:

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

                sent_email.add(row["Email"])

def get_message():
    subject = "Emergency Communications System"
    message = f"Hello {row["First_Name"]}, \n" 
    message += "This is a test of the Westmond Ward, Emergency Communications System. \n"
    message += "If this had been an actual emergency, you would have been instructed on how to respond. \n"
    message += "This is only a test. \n"

    return subject, message

sent_email = set()
sent_texts = set()
sent_voice = set()

# CSV file path
data_path = "Westmond_Master.csv"

# Read the CSV file
df = pd.read_csv(data_path)
df_filtered = df[(df['Age'] > 18)]
df_sorted = df_filtered.sort_values(by='Last_Name', ascending=True)

with open('DO_NOT_SEND.txt', 'r') as file:
    sent_texts = set(line.strip() for line in file)

for index,row in df_sorted.iterrows():

    print(row["Last_Name"],row["First_Name"])
    print(row["Phone Number"])

    #if row["Last_Name"] == "Thelin" and row["First_Name"] == "David":
    if row["Last_Name"] == "Reese" and row["First_Name"] == "Dale":

        subject, message = get_message()
        send_email(row['Email'], subject, message)
        send_texts(row['Phone Number'], message)
        send_voice(row['Phone Number'], message)

    time.sleep(.25)
