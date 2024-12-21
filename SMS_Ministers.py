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
import sys

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid= os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"
Client = Client(account_sid, auth_token)

sent_texts = set()
sent_email = set()

x=0

if len(sys.argv) > 2:
    arg1 = sys.argv[1]
    
if len(sys.argv) > 1:
    arg2 = sys.argv[2]
    district = {
        '+15099902828': 'D1',
        '+19722819991': 'D2',
        '+12086103066': 'D3',
        '+12086102929': 'SD1',
        '+12089201618': 'SD2',
        '+15093449400': 'SD3'
    }.get(arg2) 

with open('DO_NOT_SEND.txt', 'r') as file:
    sent_texts = set(line.strip() for line in file)

def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15)
    return send_at
    
def send_text(text_nbr, message):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
      try:
          send_at = get_send_time()
          message = Client.messages.create(
          body=message,
          from_=twilio_number,
          to=text_nbr,
          messaging_service_sid=messaging_sid,
          send_at=send_at.isoformat(),
          schedule_type="fixed"
          )
          sent_texts.add(text_nbr)
          return message  # Return the message object
      except Exception as e:
          print(f"Error sending SMS to {text_nbr}: {e}")
          return None  # Return None to indicate failure
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

sent_to = "Your message has been sent to the following:\n"

df = pd.read_csv("Westmond_Master.csv") 

if district and district[0] == 'S':
    df_filtered = df[(df['S_District'] == district) & (df['Age'] > 17)]
    r = range(3, 5)  
else:
    df_filtered = df[(df['B_District'] == district) & (df['Age'] > 17)]
    r = range(1, 3)

for x in r: 
    
    ministerx = f"Minister{x}"
    ministerx_phone = f"Minister{x}_Phone"
    ministerx_email = f"Minister{x}_Email"

    df_filtered = df_filtered[df_filtered[ministerx].notnull()]
    df_filtered[ministerx] = df_filtered[ministerx].fillna('')

    try:
        df_filtered[['Minister_Last', 'Minister_First']] = df_filtered[ministerx].str.split(',', expand=True) 
    except AttributeError as e:
        print(f"Error splitting {ministerx} for potential missing or invalid data: {e}")
        continue  # Skip to the next iteration of the outer for loop

    grouped_df = df_filtered.groupby(["Minister_Last", "Minister_First", ministerx_phone, ministerx_email])

    for (minister_last, minister_first, minister_phone, minister_email), group in grouped_df:
  
        text_nbr = minister_phone
        subj="Your Ministering Families"

        if x < 3:
            Bro_Sis = "Brother"
            min_org = "Elders Quorum Presidency"
        else:
            Bro_Sis = "Sister"
            min_org = "Relief Society Presidency"

        msg = f"{Bro_Sis} {minister_last}, \n"
        msg += f"{arg1}\n\n"
        # msg += f"Your {min_org},\n\n"
        
        msg += f"{minister_first.strip()}, just tap on the phone numbers below for options on ways to message them.\n\n"
        # msg += f"{minister_phone}\n\n"

        if not group.empty:
            for index, row in group.iterrows():
                msg += f"{row['Name']}"
                if not pd.isna(row['Phone Number']):
                    msg += f"  - {row['Phone Number']}"
                msg += "\n"

        # if minister_last == "Reese":
            print(minister_phone,"  " ,minister_email,msg)
            send_text(text_nbr,msg)
            # send_email(minister_email,subj,msg)
            sent_to += f"{minister_last}, {minister_first}\n"

sent_to += "You may cancel these messages by sending the following 1-word text within 10 minutes. 'cancel-sms'"
message = Client.messages.create(
body= sent_to,
from_='+12086034040',
to = arg2
)
message = Client.messages.create(
body=f'Messages have been scheduled by {arg2}',
from_='+12086034040',
to = '+15099902828'
)
