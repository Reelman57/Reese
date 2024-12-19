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

from Twilio_Mods import twilio_creds
from Twilio_Mods import get_send_time
from Twilio_Mods import send_text
from Twilio_Mods import send_voice
from Twilio_Mods import send_email
from Twilio_Mods import get_data

twilio_creds()

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

data_path = "Westmond_Master.csv"
sent_texts = set()
sent_voice = set()
sent_email = set()
x=0

df = pd.read_csv(data_path)
df_filtered = df[(df['Age'] > 17)]
df_sorted = df_filtered.sort_values(by='Last_Name', ascending=True)
    
for index,row in df_sorted.iterrows():
    if row["Last_Name"] == "Reese" and row["First_Name"] == "Dale":

        print(x, row["Last_Name"], row["First_Name"], row["Phone Number"])
    
        subject, message = get_message(row)
        
        send_email(row['Email'], subject, message, sent_email)
        sent_email.add(row["Email"])
        
        send_text(row['Phone Number'], message, sent_texts, Client)
        sent_texts.add(row["Phone Number"])
        
        send_voice(row['Phone Number'], message, sent_voice, Client)
        sent_voice.add(row["Phone Number"])
        
    x+=1
    time.sleep(.05)

message = client.messages.create(
body=f'Message sent to {x} individuals.',
from_='+12086034040',
to = arg2
)
