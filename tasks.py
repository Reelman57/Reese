# tasks.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from xml.sax.saxutils import escape
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from twilio.rest import Client

account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = "+12086034040"
client = Client(account_sid, auth_token)

# --- Your Task Functions ---

def send_emails(subject, body, data_list):
   sent_emails = set()
   try:
      with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
         smtp.starttls()
         smtp.login(os.environ.get('EMAIL_ADDRESS'), os.environ.get('EMAIL_PASSWORD'))
           
         for data in data_list:
            email = data.get('E-mail')
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
#----------------------------------------------------------------------------------------------------------------------------
def send_voice(msg_in, data_list):
    
    unique_recipients = list({data['Phone Number']: data for data in data_list if not pd.isna(data.get('Phone Number'))}.values())

    def place_one_call(data):
        try:
            to_number = data.get('Phone Number')
            
            raw_msg = f"Hello {data.get('First_Name', 'Friend')},\n{msg_in}\n"
            safe_msg = escape(raw_msg)
            
            twiml_payload = f"<Response><Pause length=\"3\"/><Say voice=\"Google.en-US-Standard-J\">{safe_msg} Goodbye. </Say></Response>"
            
            call = client.calls.create(
                twiml=twiml_payload,
                to=to_number,
                from_=twilio_number
            )
            print("Voice - ", data.get('Last_Name'), "-", to_number, f"(SID: {call.sid})")
            return call
        except Exception as e:
            print(f"Error sending voice call to {data.get('Phone Number')}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(place_one_call, unique_recipients))
    
    successful_calls = [call for call in results if call is not None]
    
    return successful_calls
