from itertools import count
from datetime import datetime, timedelta
import os
import re
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import numpy as np
import pytz
import phonenumbers
from flask import Flask, request, make_response
from twilio.rest import Client

app = Flask(__name__)
global twilio_number
# account_sid = os.environ['TWILIO_TEST_SID']
# auth_token = os.environ['TWILIO_TEST_TOKEN']
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid = os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"
# twilio_number = "+15005550006"

client = Client(account_sid, auth_token)

# --------------------------------------------------------------------------
def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15, seconds = x)
    return send_at.isoformat()
# --------------------------------------------------------------------------
def send_text(text_nbr, message, now):
    global sent_texts
    global x
    if text_nbr not in sent_texts and not pd.isna(text_nbr):
        if not now:
            send_at = get_send_time()
            schedule_type = "fixed"
        else:
            send_at = None
            schedule_type = None

        try:
            message = client.messages.create(
                body=message,
                from_=twilio_number,
                to=text_nbr,
                messaging_service_sid=messaging_sid,
                send_at=send_at,
                schedule_type=schedule_type
            )
            sent_texts.add(text_nbr)
            x+=1
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
def sms_send(msg_in, data_list, now):
    success_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for data in data_list:
            msg = f"Hello {data['First_Name']},\n{msg_in}\n"
            future = executor.submit(send_text, data['Phone Number'], msg, now)
            futures.append(future)
            print("SMS - ", data['Last_Name'], "-", data['Phone Number'])

        for future in futures:
            try:
                result = future.result()
                if result:
                    success_count += 1
            except Exception as e:
                app.logger.error(f"Error processing future: {e}")
    
    return success_count
# -------------------------------------------------------------------------- 
@app.route("/sms", methods=['POST'])        
def incoming_sms():
    authorized_list = [
        '+15099902828',
        '+19722819991',
        '+12086103066',
        '+12086102929',
        '+12089201618',
        '+15093449400'
    ]
    message_body = request.values.get('Body', None)
    global from_number
    from_number = request.values.get('From', None)
    data_file = "Westmond_Master.csv"
    data_list = process_data(data_file)

    if message_body is None or from_number is None:
        return "Invalid request: Missing message body or sender number", 400

    first_word = message_body.split()[0].lower()
    msg_in = message_body.strip()
    lines = msg_in.splitlines()

    if len(lines) > 1:
        msg_in = "\n".join(lines[1:])
        
    global sent_texts        
    sent_texts = set()
    try:
        with open('DO_NOT_SEND.txt', 'r') as file:
            sent_texts = set(line.strip() for line in file)
    except FileNotFoundError:
        return "Error: DO_NOT_SEND.txt file not found.", 500

    global x
    x = 0
# --------------------------------------------------------------------------
    if first_word == "sms77216" and from_number in authorized_list:
        sms_send(msg_in, data_list, False)
        confirm_send()
        return "SMS messages scheduled.", 200
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
        return f'{canceled_count} messages canceled.', 200
# --------------------------------------------------------------------------
    elif first_word == "ecs77216" and (from_number in authorized_list or from_number == '+13607428998'):
        subject = "Emergency Communications System"
        sms_send(msg_in, data_list, True)
        send_email(subject, msg_in, data_list)
        send_voice(msg_in, data_list)
        confirm_send()
        return "Emergency Communications System messages sent.", 200
# --------------------------------------------------------------------------
    elif first_word == "eld77216" and from_number in authorized_list:
        try:
            df = pd.read_csv(data_file)
        except FileNotFoundError:
            return "Error: File not found.", 500
        except Exception as e:
            return f"Error reading data file: {e}", 500

        try:
            df_filtered = df[df['Age'] > 17]
            df_filtered = df_filtered[df_filtered['Gender'] == "M"]
            df_filtered = df_filtered[['First_Name', 'Last_Name', 'Phone Number', 'Email']]
            df_filtered = df_filtered.dropna(subset=['Phone Number'])
            df_filtered['is_valid_phone'] = df_filtered['Phone Number'].apply(lambda x: is_valid_phone_number(x))
            df_filtered = df_filtered[df_filtered['is_valid_phone']]
            df_filtered = df_filtered.drop_duplicates(subset=['Phone Number'])

            data_list = df_filtered.to_dict('records')

            ministers = set(df['Minister1_Phone'].dropna().tolist() + df['Minister2_Phone'].dropna().tolist())
    
            for data in data_list:
                if data['Phone Number'] in ministers:
                    print(f"{x}. {data['First_Name']} {data['Last_Name']}")
                    msg = f"Brother {data['Last_Name']}, \n\n"
                    msg += msg_in
                    send_text(data['Phone Number'], msg, False)
    
        except Exception as e:
             return f"An error occurred while processing the request: {e}", 500

        confirm_send()
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "min77216" and from_number in authorized_list:
        district = {
            '+15099902828': 'D1',
            '+19722819991': 'D2',
            '+12086103066': 'D3',
            '+12086102929': 'SD1',
            '+12089201618': 'SD2',
            '+15093449400': 'SD3'
        }
        district = district.get(from_number)

        try:
            df = pd.read_csv(data_file)
        except FileNotFoundError:
            return "Error: File not found.", 500
        except Exception as e:
            return f"Error reading data file: {e}", 500
        
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
                else:
                    Bro_Sis = "Sister"
                    
                msg = f"{Bro_Sis} {minister_last}, \n"
                msg += f"{msg_in} \n\n"
                msg += f"{minister_first.strip()}, just tap on the phone numbers below for options on ways to message them.\n\n"
        
                if not group.empty:
                    for index, row in group.iterrows():
                        msg += f"{row['Name']}"
                        if not pd.isna(row['Phone Number']):
                            msg += f"  - {row['Phone Number']}"
                        msg += "\n"
        
                    print(minister_phone,"  " ,minister_email,msg)
                    send_text(text_nbr, msg, False)
                    # send_email(minister_email,subj,msg)

        confirm_send()
        return "Ministering district messages sent.", 200
# --------------------------------------------------------------------------
    elif (first_word == "?" or first_word == "instructions") and from_number in authorized_list:
        instructions = "To send a message to any of the following groups.  Simply type the group code on the 1st line followed by your message on subsequent lines.  The message will already have a salutation on it, ie. 'Brother Jones' or 'Hello John'.  Do not use emojis or pictures.  The app is authenticated by your phone number and will only work on your phone.\n\n"
        instructions += "Group codes\n"
        instructions += "min77216 - Your Ministering District with assignments\n"
        instructions += "eld77216 - Active Adult Priesthood holders\n"
        instructions += "sms77216 - Entire Ward\n\n"
        instructions += "These messages have a 15 minute delay before they go out.  Should you choose to cancel them you may send the command 'cancel-sms' within that 15 minutes"

        message = client.messages.create(
            body= instructions,
            from_='+12086034040',
            to = from_number
            )
# --------------------------------------------------------------------------
    elif first_word == "dnc77216" and from_number in authorized_list:
        do_not_send_file = "DO_NOT_SEND.txt"
        data_file = "Westmond_Master.csv"
    
        try:
            with open(do_not_send_file, 'r') as f:
                do_not_send_numbers = set(line.strip() for line in f)
    
            df = pd.read_csv(data_file)
            matching_numbers = df[df['Phone Number'].isin(do_not_send_numbers)]
            names = matching_numbers[['First_Name', 'Last_Name']].values.tolist() 
    
        except FileNotFoundError:
            print(f"Error: File not found: {do_not_send_file} or {data_file}")
            return "Error: File not found.", 500 
        except Exception as e:
            print(f"An error occurred: {e}")
            return "An error occurred.", 500
    
        if names:
            message = "Names associated with phone numbers in DO_NOT_SEND.TXT:\n"
            for name in names:
                message += f"{name[0]} {name[1]}\n" 
            
            client.messages.create(
                body=message,
                from_=twilio_number,
                to=from_number
            )
            return "List of names sent successfully.", 200
        else:
            client.messages.create(
                body="No matching phone numbers found.",
                from_=twilio_number,
                to=from_number
            )
            return "No matching phone numbers found.", 200
# --------------------------------------------------------------------------
else:
        client.messages.create(
        body=msg_in,
        from_=twilio_number,
        to='+15099902828'
    )
    return "Command not recognized or unauthorized.", 400
# --------------------------------------------------------------------------
def confirm_send():
    client.messages.create(
        body=f"{x} Messages scheduled. Send 'cancel-sms' within 10 mins to cancel them",
        from_=twilio_number,
        to=from_number
    )
    client.messages.create(
        body=f'{x} Messages have been scheduled by {from_number}',
        from_=twilio_number,
        to='+15099902828'
    )

if __name__ == "__main__":
    app.run()
