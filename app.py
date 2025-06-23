from itertools import count
from datetime import datetime, timedelta
import os
import re
import csv
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
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid = os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"

client = Client(account_sid, auth_token)
x=0
sent_texts = set()

# --------------------------------------------------------------------------
def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15, seconds = x)
    return send_at.isoformat()
# --------------------------------------------------------------------------
def send_text(text_nbr, message, now):
    global x 
    global sent_texts 

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
        if email not in sent_emails and not pd.isna(email):
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
    df_filtered = df_filtered[['Name','Household','First_Name', 'Last_Name', 'Phone Number', 'E-mail', 'Gender','District','Minister1','Minister2','Minister3']]
    #df_filtered = df_filtered.dropna(subset=['Phone Number'])
    #df_filtered['is_valid_phone'] = df_filtered['Phone Number'].apply(lambda x: is_valid_phone_number(x))
    #df_filtered = df_filtered[df_filtered['is_valid_phone']]
    df_filtered = df_filtered.drop_duplicates(subset=['Phone Number'])
    
    with open('DO_NOT_SEND.txt', 'r') as f:
        do_not_send_numbers = set(line.strip() for line in f)
    df_filtered = df_filtered[~df_filtered['Phone Number'].isin(do_not_send_numbers)]

    data_list = df_filtered.to_dict('records')
    return data_list
    
def filter_minister(data_list):
  return [record for record in data_list if record.get('Minister1')]

def filter_gender(data_list, gender):
    return [record for record in data_list if record.get('Gender') == gender]
# --------------------------------------------------------------------------    
def is_valid_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number, region="US")
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False
# --------------------------------------------------------------------------
def sms_send(msg_in, data_list, now, prepared_messages=None):
    """
    Sends SMS messages concurrently.

    Can operate in two modes:
    1. Standard Mode: Sends a template message (`msg_in`) to a `data_list`,
       personalizing with the first name.
    2. Prepared Mode: Sends a list of `prepared_messages`, where each
       item is a dictionary with the phone number and the full message body.
    """
    success_count = 1
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        sendnow = now

        if prepared_messages:
            # Mode 2: Iterate over pre-rendered messages
            for item in prepared_messages:
                # The 'phone' and 'message' keys must be in the dictionary
                future = executor.submit(send_text, item.get('phone'), item.get('message'), sendnow)
                futures.append(future)
                print("SMS (Prepared) - ", item.get('phone'))
        elif data_list:
            # Mode 1: Original behavior
            for data in data_list:
                msg = f"Hello {data['First_Name']},\n{msg_in}\n"
                future = executor.submit(send_text, data['Phone Number'], msg, sendnow)
                futures.append(future)
                print("SMS - ", data['Last_Name'], "-", data['Phone Number'])

        for future in futures:
            try:
                result = future.result()
                if result:
                    success_count += 1
            except Exception as e:
                # It's good practice to log errors, especially in threads
                print(f"Error processing a sending future: {e}")

    return success_count
# --------------------------------------------------------------------------
def get_minister_phone_number(minister_name_to_lookup):
    
    if not os.path.exists(data_file):
        print(f"Error: Merged file not found at {data_file}. Please run the main script first to create it.")
        return []
    try:
        merged_df = pd.read_csv(data_file)
    except Exception as e:
        print(f"Error loading merged file {data_file}: {e}")
        return []

    required_cols = ['Name', 'Phone Number'] # Adjust 'Phone Number' if your column name is different
    if not all(col in merged_df.columns for col in required_cols):
        print(f"Error: One or more required columns ({required_cols}) not found in the merged file.")
        print(f"Available columns in '{data_file}': {merged_df.columns.tolist()}")
        return []

    minister_records = merged_df[
        merged_df['Name'].astype(str).str.strip().str.lower() == minister_name_to_lookup.strip().lower()
    ]

    if minister_records.empty:
        print(f"Minister '{minister_name_to_lookup}' not found in the 'Name' column of '{data_file}'.")
        return []

    # Extract unique phone numbers, drop any NaN/empty values, and convert to list of strings
    phone_numbers = minister_records['Phone Number'].dropna().astype(str).unique().tolist()

    return phone_numbers
# --------------------------------------------------------------------------
def get_unitnbr(from_number, filename="User_UnitNbr.csv"):
    global district_code
    district_code = None
    global district_ldr
    district_ldr = None
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if len(row) >= 2: 
                    first_column_value = row[0].strip()
                    unit_nbr = row[1].strip()
                    district_code = row[3].strip() if len(row) > 2 else None
                    district_ldr = row[2].strip()

                if first_column_value == from_number:
                    return unit_nbr, district_code, district_ldr

        print(f"No unit number found for '{from_number}' in '{filename}'.")
        return None

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the CSV: {e}")
        return None
# --------------------------------------------------------------------------
def get_phone_number_by_name(df, minister_name):
    minister_name_str = str(minister_name).strip().lower()
    match = df[df['Name'].astype(str).str.strip().str.lower() == minister_name_str]
    if not match.empty and 'Phone Number' in match.columns and pd.notna(match['Phone Number'].iloc[0]):
        return str(match['Phone Number'].iloc[0]).strip()
    return None
# --------------------------------------------------------------------------
def get_unique_unitnbr_list(csv_path):
    df = pd.read_csv(csv_path)
    if 'UnitNbr' not in df.columns:
        raise ValueError("Column 'UnitNbr' not found in the CSV file.")
    return df['UnitNbr'].dropna().unique().tolist()
# --------------------------------------------------------------------------
def find_member_by_phone(unitnbr_list, from_number):
    results = []
    for unitnbr in unitnbr_list:
        members_file = os.path.join(f"{unitnbr}_datafile.csv")
        if not os.path.exists(members_file):
            print(f"Members file not found for unit {unitnbr}: {members_file}")
            continue
        df = pd.read_csv(members_file)
        # Normalize phone numbers for comparison
        df['Phone Number'] = df['Phone Number'].astype(str).str.replace(r'\D', '', regex=True)
        search_number = re.sub(r'\D', '', str(from_number))
        match = df[df['Phone Number'] == search_number]
        if not match.empty:
            row = match.iloc[0]
            results.append([
                unitnbr,
                row['Phone Number'],
                f"{row['First_Name']} {row['Last_Name']}"
            ])
    return results
# --------------------------------------------------------------------------
def format_phone_number(phone):
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return as-is if not a standard US number
# --------------------------------------------------------------------------
def confirm_send():
    global x
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
# --------------------------------------------------------------------------
def is_user_authenticated(from_number, csv_path="User_UnitNbr.csv"):
    
    df = pd.read_csv(csv_path)
    if from_number in df['UserPhone'].values:
        print(f"Authentication successful for {from_number}")
        return True
    else:
        print(f"Authentication failed for {from_number}")
        return False
# --------------------------------------------------------------------------
@app.route("/sms", methods=['POST'])

def incoming_sms():
    
    message_body = request.values.get('Body', None)
    global from_number
    global data_file
    
    from_number = request.values.get('From', None)
    from_number = format_phone_number(from_number)

    if message_body is None or from_number is None:
        resp = MessagingResponse()
        resp.message("Invalid request: Missing message body or sender number.")
        return str(resp), 400

    first_word = message_body.split()[0].lower()
    msg_in = message_body.strip()
    lines = msg_in.splitlines()

    if len(lines) > 1:
        msg_in = "\n".join(lines[1:])
    
    with open('DO_NOT_SEND.txt', 'r') as file:
        sent_texts = set(line.strip() for line in file)

    time.sleep(2)
    
    if is_user_authenticated(from_number):
        
        unit_nbr = get_unitnbr(from_number)
        data_file = unit_nbr[0] + "_datafile.csv"
        data_list = process_data(data_file)
    # --------------------------------------------------------------------------
        if first_word == "ward"+unit_nbr[0]:
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
        elif first_word == "emergency"+unit_nbr[0]:
            subject = "Emergency Communications System"
            send_voice(msg_in, data_list)
            sms_send(msg_in, data_list, True)
            send_email(subject, msg_in, data_list)
            confirm_send()
            return "Emergency Communications System messages sent.", 200
    # --------------------------------------------------------------------------
        elif first_word == "elders"+unit_nbr[0]:
            filtered_data_list = filter_gender(data_list, "M")
            
            for data in filtered_data_list:
                msg = f"Brother {data['Last_Name']}, \n\n"
                msg += msg_in
                send_text(data['Phone Number'], msg, False)
    
            confirm_send()
            return "Messages sent successfully.", 200
    # --------------------------------------------------------------------------
        elif first_word == "sisters"+unit_nbr[0]:
            filtered_data_list = filter_gender(data_list, "F")
            
            for data in filtered_data_list:
                msg = f"Sister {data['Last_Name']}, \n\n"
                msg += msg_in
                send_text(data['Phone Number'], msg, False)
    
            confirm_send()
            return "Messages sent successfully.", 200
    # --------------------------------------------------------------------------
        elif first_word == "families"+unit_nbr[0]:
            filtered_data_list = filter_minister(data_list)
            
            # Create a list to hold the dictionaries of prepared messages
            messages_to_send = []
    
            for data in filtered_data_list:
                # Determine the correct salutation
                if data.get('Gender') == "M":
                    msg = f"Brother {data['Last_Name']},\n\n"
                elif data.get('Gender') == "F":
                    msg = f"Sister {data['Last_Name']},\n\n"
                else:
                    msg = f"{data['First_Name']} {data['Last_Name']},\n\n"
    
                msg += "Your assigned ministering brothers are as follows:\n"
    
                # Loop through ministers and add their details
                for i in range(1, 4):
                    minister_col = f'Minister{i}'
                    if pd.notna(data.get(minister_col)):
                        minister_name = data[minister_col]
                        msg += f"- {minister_name}"
                        phone_numbers = get_minister_phone_number(minister_name)
                        if phone_numbers:
                            # Format and join multiple numbers if a minister has them
                            formatted_numbers = [format_phone_number(p) for p in phone_numbers]
                            msg += f": {', '.join(formatted_numbers)}"
                        msg += "\n"
    
                msg += "\nFeel free to reach out to them for Priesthood blessings, spiritual guidance, physical assistance or any other needs you might have.\n"
                msg += "If you are unable to reach your Ministering Brothers then please contact a member of the Elders Quorum Presidency.\n"
    
                # Add the recipient's phone number and the fully formed message to our list
                if data.get('Phone Number') and not pd.isna(data.get('Phone Number')):
                    messages_to_send.append({
                        'phone': data['Phone Number'],
                        'message': msg
                    })
    
            sms_send(msg_in=None, data_list=None, now=False, prepared_messages=messages_to_send)
    
            confirm_send()
            return "Messages sent successfully.", 200
    # --------------------------------------------------------------------------
        elif first_word == "ministering"+unit_nbr[0]:
    
            df = pd.read_csv(data_file)
            df_filtered = df[df['Age'] > 17]
            df_filtered = df_filtered[['Name','Household','First_Name', 'Last_Name', 'Phone Number', 'E-mail', 'Gender','District','Minister1','Minister2','Minister3']]
           
            data_list = df_filtered.to_dict('records')
            
            filtered_data_list = filter_minister(data_list)
            df = pd.DataFrame(filtered_data_list)
            
            df['Minister1'] = df['Minister1'].fillna('')
            df['Minister2'] = df['Minister2'].fillna('')
            df['Minister3'] = df['Minister3'].fillna('')
            
            grouped = df.groupby(['Minister1', 'Minister2', 'Minister3'])
            
            for group_keys, group_df in grouped:
                family_names = group_df[['First_Name', 'Last_Name', 'Phone Number']].apply(
                    lambda row: f"{row['First_Name']} {row['Last_Name']}" +
                    (f" - {row['Phone Number']}" if pd.notna(row['Phone Number']) and str(row['Phone Number']).strip() != '' else " - "),
                    axis=1
                ).tolist()
                family_list_str = "\n".join(family_names)
            
                # group_keys is a tuple: (Minister1, Minister2, Minister3)
                for minister in group_keys:
                    if pd.isna(minister) or not minister:
                        continue
            
                    # Name parsing as before
                    if "," in minister:
                        parts = minister.split(",", 1)
                        last_name = parts[0].strip()
                        first_middle = parts[1].strip()
                        first_name = first_middle.split()[0] if first_middle else ""
                    else:
                        last_name = minister.strip()
                        first_name = ""
            
                    # Companions: the other two ministers in this group
                    companions = [m for m in group_keys if m != minister and pd.notna(m) and m]
                    companions_formatted = []
                    for comp in companions:
                        if "," in comp:
                            comp_parts = comp.split(",", 1)
                            comp_last = comp_parts[0].strip()
                            comp_first = comp_parts[1].strip().split()[0] if len(comp_parts) > 1 else ""
                            companions_formatted.append(f"{comp_first} {comp_last}")
                        else:
                            companions_formatted.append(comp.strip())
                    companions_str = ", ".join(companions_formatted) if companions_formatted else "None"
            
                    msg = f"Brother {last_name},\n"
                    msg += f"{msg_in}\n\n"
                    msg += f"These are the individuals you have been assigned to:\n{family_list_str}\n\n"
                    msg += f"Your Companion(s) are: {companions_str}\n\n"
                    msg += "Do not respond to this automated message but you can reach me at: \n"
                    msg += f"{from_number},\n"
                    msg += f"{district_ldr}\n"
            
                    phone_number = get_phone_number_by_name(df, minister)
                    if phone_number:
                        send_text(phone_number, msg, False) 
            confirm_send()            
            resp = MessagingResponse()
            resp.message("Your message was processed successfully!")
            return str(resp), 200    
    # --------------------------------------------------------------------------
        else: # This 'else' handles UNRECOGNIZED commands from an AUTHENTICATED user
            # Alert the admin about the unrecognized command
            reply = (f"Authenticated user {from_number} sent an unrecognized command:\n\n"
                     f"{message_body}")
            
            client.messages.create(
                body=reply,
                from_=twilio_number,
                to='+15099902828'
            )
            
            # Best practice: Inform the user their command was not recognized
            resp = MessagingResponse()
            resp.message(f"Command not recognized. Please check the command and try again.")
            return Response(str(resp), mimetype="application/xml")

    else:

        unitnbr_list = get_unique_unitnbr_list(os.path.join("User_UnitNbr.csv"))
        matches = find_member_by_phone(unitnbr_list, from_number)
        if matches:
            # Format each match as a readable string
            reply = "\n".join(f"Unit: {m[0]}, Phone: {m[1]}, Name: {m[2]}" for m in matches)
            reply += "\n"
            reply += msg_in
        else:
            reply = f"No matching member found for ",{from_number}
        
        try:
            client.messages.create(
                body=reply,
                from_=twilio_number,
                to='+15099902828'
            )
        except Exception as e:
            pass
        return Response("<Response></Response>", mimetype="application/xml")
# --------------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
