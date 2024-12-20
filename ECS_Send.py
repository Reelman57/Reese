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

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid= os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"
Client = Client(account_sid, auth_token)

sent_texts = set()
sent_voice = set()
sent_email = set()

x=0

if len(sys.argv) > 1:
    arg1 = sys.argv[1]
else:
    arg1 = ""

if len(sys.argv) > 2:
    arg2 = sys.argv[2]
else:
    arg2 = "+15099902828"

with open('DO_NOT_SEND.txt', 'r') as file:
    sent_texts = set(line.strip() for line in file)

def send_text(text_nbr, message):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        message = Client.messages.create(
            body=message,
            from_=twilio_number,
            to=text_nbr
        )
        
def get_message(row):
    subject = "Emergency Communications System"
    message = f"Hello {row['First_Name']},\n"

    if arg1:
        message += arg1 + "\n"
    else:
        message += "This is a test of the Westmond Ward, Emergency Communications System.\n"
        message += "If this had been an actual emergency, you would have been instructed on how to respond.\n"
        message += "This is only a test.\n"

    return subject, message

def send_text(text_nbr, message):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        message = Client.messages.create(
            body=message,
            from_=twilio_number,
            to=text_nbr
        )
        sent_texts.add(row["Phone Number"])
        
def send_voice(to_number, message):
    if to_number not in sent_voice and not pd.isna(to_number):
        call = Client.calls.create(
            twiml = "<Response><Pause length=\"3\"/><Say voice=\"Google.en-US-Standard-J\">" + message + "Goodbye. </Say></Response>",
            to=to_number,
            from_=twilio_number
        )
        sent_voice.add(row["Phone Number"])
        
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

            sent_email.add(row["Email"])

data_path = "Westmond_Master.csv"

df = pd.read_csv(data_path)
df_filtered = df[(df['Age'] > 17)]
df_sorted = df_filtered.sort_values(by='Last_Name', ascending=True)
    
for index,row in df_sorted.iterrows():
    if row["Last_Name"] == "Reese" and row["First_Name"] == "Dale":

        print(x, row["Last_Name"], row["First_Name"], row["Phone Number"])
    
        subject, message = get_message(row)
        
        send_email(row['Email'], subject, message, sent_email)
        send_text(row['Phone Number'], message, sent_texts, Client)
        send_voice(row['Phone Number'], message, sent_voice, Client)
        
    x+=1
    time.sleep(.05)

message = Client.messages.create(
body=f'Message sent to {x} individuals.',
from_='+12086034040',
to = arg2
)
