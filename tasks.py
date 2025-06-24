# tasks.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from xml.sax.saxutils import escape

import pandas as pd
from twilio.rest import Client

# --- Initialize clients and variables needed ONLY by the tasks ---
# It's good practice for tasks to be self-contained.
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = "+12086034040"
client = Client(account_sid, auth_token)

# --- Your Task Functions ---

def send_emails(subject, body, data_list):
   
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(os.environ.get('EMAIL_ADDRESS'), os.environ.get('EMAIL_PASSWORD'))
            
            for data in data_list:
                email = data.get('Email')
                if email not in sent_emails and not pd.isna(email):
                    try:
                        message = f"Hello {data.get('First_Name', 'Friend')},\n{body}\n"
                        msg = MIMEMultipart()
                        msg['From'] = os.environ.get('EMAIL_ADDRESS')
                        msg['To'] = email
                        msg['Subject'] = subject
                        msg.attach(MIMEText(message, 'plain'))
                        smtp.sendmail(msg['From'], msg['To'], msg.as_string())
                        sent_emails.add(email)
                        print("Email - ", data.get('Last_Name'), "-", email)
                    except Exception as e:
                        print(f"Error sending individual email to {email}: {e}")
    except Exception as e:
        print(f"Failed to connect or login to SMTP server: {e}")
    return len(sent_emails)


def send_voice(msg_in, data_list):
    """
    The concurrent voice call function. (This is a simplified placeholder, use your full function)
    """
    print(f"Starting to place voice calls for message: {msg_in[:30]}...")
    # ... your full send_voice_concurrent logic goes here ...
    # This example just prints, but you would have your real function.
    print(f"Finished placing {len(data_list)} voice calls.")
    return len(data_list)
