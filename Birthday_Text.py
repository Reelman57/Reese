from itertools import count
import pandas as pd
import numpy as np
from datetime import datetime
from twilio.rest import Client
import time
import pytz
import os
from datetime import datetime, timedelta

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid= os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"

Client = Client(account_sid, auth_token)

def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=30)
    return send_at
    
def send_text(text_nbr, message):
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
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
    print (sent_texts):
    time.sleep(1)

# Read the CSV file
df = pd.read_csv('Westmond_Master.csv')      
    sent_texts = set()
    with open('DO_NOT_SEND.txt', 'r') as file:
        sent_texts = set(line.strip() for line in file)

df['Birth Date'] = pd.to_datetime(df['Birth Date'])
today = datetime.today()
today_month = today.month
today_day = today.day 

df_filtered = df[(df['Age'] > 17)
            & (df['Birth Date'].dt.day == today_day)
            & (df['Birth Date'].dt.month == today_month)]

for index, row in df_filtered.iterrows():
    name = row['First_Name'] + ' ' + row['Last_Name']
    fname = row['First_Name']

    if row['Gender'] == 'M':
        pronoun = 'him'
        pronoun2 = "his"
        UC_pronoun2 = "His"
        min_gend = "Brother"
        min_org = "Westmond Ward\n" \
        "Elder's Quorum Presidency\n\n"

    elif row['Gender'] == 'F':
        pronoun = 'her'
        pronoun2 = "her"
        UC_pronoun2 = "Her"
        min_gend = "Sister"
        min_org = "Westmond Ward\n"  \
        "Relief Society Presidency\n\n"

    Bishopric = ['+1 (208) 627-2451','+1 (208) 277-5613','+1 (801) 673-1861']

    Ministers12 = []
    Ministers34 = []
    Ministers12 = [f", {minister}" for minister in [row['Minister1_Phone'], row['Minister2_Phone']] if not pd.isna(minister)]
    Ministers34 = [f", {minister}" for minister in [row['Minister3_Phone'], row['Minister4_Phone']] if not pd.isna(minister)]

    ReliefSociety = ['+1 (208) 610-2929','+1 (208) 920-1618', '+1 (509) 344-9400','+1 (310) 570-9897']

    #Birthday Person

    if not pd.isna(row['Phone Number']):
        phone = row['Phone Number']
        phone_number = row['Phone Number']

        msg = f"Happy Birthday {fname}!\n\n" 
        msg += "We hope you have a wonderful day. " 
        msg += "Please let us know if there is anything we can do to help make it so.\n\n"
        msg += min_org
        
        send_text(phone_number,msg)

    else:
        phone = "not listed in LDS Tools"

    #Ministering Brothers

    msg = f"A person whom you minister to, {name}, has a birthday today. {UC_pronoun2} phone number is {phone}\n"
    msg += f"Just click on {pronoun2} number for options on ways to message {pronoun}.\n\n"

    for phone_number in Ministers12:

        send_text(phone_number,msg)

    #Ministering Sisters

    if row['Gender'] == 'F':

        msg = f"A person whom you minister to, {name}, has a birthday today. {UC_pronoun2} phone number is {phone}\n"
        msg += f"Just click on {pronoun2} number for options on ways to message {pronoun}.\n\n"

        for phone_number in Ministers34:

            send_text(phone_number,msg)

    #Bishopric

    msg = f"{name} has a birthday today, {pronoun2} phone number is {phone}\n\n"
    msg += f"Just click on {pronoun2} number for options on ways to message {pronoun}.\n\n"

    for phone_number in Bishopric:

        send_text(phone_number,msg)

    #Relief Society

    if row['Gender'] == 'F':

        msg = f"{name} has a birthday today, {pronoun2} phone number is {phone}\n\n"
        msg += f"Just click on {pronoun2} number for options on ways to message {pronoun}.\n\n"

        for phone_number in ReliefSociety:

            send_text(phone_number,msg)
