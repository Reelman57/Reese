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
arg1 = sys.argv[1] if len(sys.argv) > 1 else ""
arg2 = sys.argv[2] if len(sys.argv) > 2 else "+15099902828"

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

def send_text(text_nbr, message):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        try:
            message = Client.messages.create(
                body=message,
                from_=twilio_number,
                to=text_nbr
            )
            sent_texts.add(text_nbr)  # Add the actual phone number to the set
            return message  # Return the message object
        except Exception as e:
            print(f"Error sending SMS to {text_nbr}: {e}")
            return None  # Return None to indicate failure
    else:
        return None 
        
def send_voice(to_number, message):
    if to_number not in sent_voice and not pd.isna(to_number):
        try:
            call = Client.calls.create(
                twiml="<Response><Pause length=\"3\"/><Say voice=\"Google.en-US-Standard-J\">" + message + " Goodbye. </Say></Response>",
                to=to_number,
                from_=twilio_number
            )
            sent_voice.add(to_number)  # Add the actual phone number to the set
            return call  # Return the call object for potential further processing
        except Exception as e:
            print(f"Error sending voice call to {to_number}: {e}")
            return None
    else:
        return None 
        
def send_email(to_addr, subject, body):
  if to_addr not in sent_email and not pd.isna(to_addr):
    if isinstance(to_addr, str):
      try:
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('EMAIL_ADDRESS')  # Use environment variable
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
          smtp.starttls()
          smtp.login(os.environ.get('EMAIL_ADDRESS'), os.environ.get('EMAIL_PASSWORD'))  # Use environment variables
          smtp.sendmail(msg['From'], msg['To'], msg.as_string())

        sent_email.add(to_addr)
        return True  # Indicate successful email sending
      except Exception as e:
        print(f"Error sending email to {to_addr}: {e}")
        return False  # Indicate failure
    else:
      print(f"Invalid email address format: {to_addr}")
      return False  # Indicate failure for invalid email format
  else:
    return False  # Indicate email not sent (already sent or invalid)

data_path = "Westmond_Master.csv"

df = pd.read_csv(data_path)
df_filtered = df[(df['Age'] > 17)]
df_sorted = df_filtered.sort_values(by='Last_Name', ascending=True)
    
for index,row in df_sorted.iterrows():
# if row["Last_Name"] == "Reese" and row["First_Name"] == "Dale":

    print(x, row["Last_Name"], row["First_Name"], row["Phone Number"])

    subject, message = get_message(row)
    
    send_email(row['Email'], subject, message)
    send_text(row['Phone Number'], message)
    send_voice(row['Phone Number'], message)
    
x+=1
time.sleep(.05)

message = Client.messages.create(
body=f'Message sent to {x} individuals.',
from_='+12086034040',
to = arg2
)
