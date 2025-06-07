holfrom itertools import count
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
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
global twilio_number
# account_sid = os.environ['TWILIO_TEST_SID']
# auth_token = os.environ['TWILIO_TEST_TOKEN']
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
messaging_sid = os.environ['TWILIO_MSGNG_SID']
twilio_number = "+12086034040"

client = Client(account_sid, auth_token)

# --------------------------------------------------------------------------
def get_send_time():
    timezone = pytz.timezone('America/Los_Angeles')
    now_utc = datetime.now(timezone)
    send_at = now_utc + timedelta(minutes=15, seconds = x)
    return send_at.isoformat()
# --------------------------------------------------------------------------
def send_text(text_nbr, message, now):
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

    if not phone_numbers:
        print(f"No phone number found for minister '{minister_name_to_lookup}' in '{data_file}'.")

    return phone_numbers
   
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
    df_filtered = df_filtered[['Household','First_Name', 'Last_Name', 'Phone Number', 'E-mail', 'Gender','District','Minister1','Minister2','Minister3']]
    df_filtered = df_filtered.dropna(subset=['Phone Number'])
    df_filtered['is_valid_phone'] = df_filtered['Phone Number'].apply(lambda x: is_valid_phone_number(x))
    df_filtered = df_filtered[df_filtered['is_valid_phone']]
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
def sms_send(msg_in, data_list, now):
    success_count = 1
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        sendnow = now
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
                app.logger.error(f"Error processing future: {e}")
    
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

    if not phone_numbers:
        print(f"No phone number found for minister '{minister_name_to_lookup}' in '{data_file}'.")

    return phone_numbers
# --------------------------------------------------------------------------
def get_unitnbr(from_number, filename="User_UnitNbr.csv"):
    global district_code
    district_code = None
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if len(row) >= 2: 
                    first_column_value = row[0].strip()
                    unit_nbr = row[1].strip()
                    district_code = row[3].strip() if len(row) > 2 else None

                if first_column_value == from_number:
                    print(f"Unit Number is {unit_nbr}")
                    print(f"District Code is {district_code}")
                    return unit_nbr, district_code

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
    record = df[df['Name'].astype(str).str.strip().str.lower() == minister_name.strip().lower()]
    if not record.empty:
        return record['Phone Number'].iloc[0]
    return None
# --------------------------------------------------------------------------
@app.route("/sms", methods=['POST'])

def incoming_sms():
    
    message_body = request.values.get('Body', None)
    global from_number
    global data_file
    global sent_texts 
    global x
    
    from_number = request.values.get('From', None)

    unit_nbr = get_unitnbr(from_number)
    if unit_nbr is None:
        alert_to_team = f"Lookup failed for {from_number}: no unit number found."

        try:
            client.messages.create(
                body=alert_to_team,
                from_=twilio_number,
                to='+15099902828' # Assuming this is the team's number
            )
            resp = MessagingResponse()
            resp.message("Sorry, I couldn't find your unit number. Please contact support.")
            return str(resp), 200 # Return TwiML with 200 OK
        except Exception as e:
            print(f"Error sending alert to team: {e}")
            return "Internal server error during alert.", 500
    
    data_file = unit_nbr[0] + "_datafile.csv"
    data_list = process_data(data_file)

    if message_body is None or from_number is None:
        resp = MessagingResponse()
        resp.message("Invalid request: Missing message body or sender number.")
        return str(resp), 400

    first_word = message_body.split()[0].lower()
    msg_in = message_body.strip()
    lines = msg_in.splitlines()

    if len(lines) > 1:
        msg_in = "\n".join(lines[1:])
        resp = MessagingResponse()
        resp.message("I processed the multi-line message. Thank you!")
        return str(resp), 200 
        
    sent_texts = set()
    
    with open('DO_NOT_SEND.txt', 'r') as file:
        sent_texts = set(line.strip() for line in file)

    x = 0
    time.sleep(2)
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
            print(f"{x}. {data['First_Name']} {data['Last_Name']} - {data['Phone Number']}")
            msg = f"Brother {data['Last_Name']}, \n\n"
            msg += msg_in
            send_text(data['Phone Number'], msg, False)

        confirm_send()
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "sisters"+unit_nbr[0]:
        filtered_data_list = filter_gender(data_list, "F")
        
        for data in filtered_data_list:
            print(f"{x}. {data['First_Name']} {data['Last_Name']} - {data['Phone Number']}")
            msg = f"Sister {data['Last_Name']}, \n\n"
            msg += msg_in
            send_text(data['Phone Number'], msg, False)

        confirm_send()
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "families"+unit_nbr[0]:
        filtered_data_list = filter_minister(data_list)

        for x, data in enumerate(filtered_data_list, start=1): 
            
            if data.get('Gender') == "M":
                msg = f"Brother {data['Last_Name']}, \n\n"
            elif data.get('Gender') == "F":
                msg = f"Sister {data['Last_Name']}, \n\n"
            else: 
                msg = f"{data['First_Name']} {data['Last_Name']}, \n\n"  # Handle cases where Gender is missing or invalid
    
            msg += "Your assigned ministering brothers are as follows: \n"
            
            for i in range(1, 4): # Loop for Minister1, Minister2, Minister3
                minister_col = f'Minister{i}'
                if pd.notna(data.get(minister_col)):
                    minister_name = data[minister_col]
                    msg += f"{minister_name}"
                    phone_numbers = get_minister_phone_number(minister_name)
                    if phone_numbers:
                        msg += f" - {', '.join(phone_numbers)}"
                    else:
                        msg += " " 
                    msg += "\n"
            
            msg += "Feel free to reach out to them for Priesthood blessings, spiritual guidance, physical assistance or any other needs you might have. \n"
            msg += "If you are unable to reach your Ministering Brothers then please contact a member of the Elders Quorum Presidency. \n"
            print(f"{x}. {data['First_Name']} {data['Last_Name']}")
            #send_text(data['Phone Number'], msg, False) 

        confirm_send() 
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "district"+unit_nbr[0]:

        data_list = process_data(data_file)
        filtered_data_list = filter_minister(data_list)
        df = pd.DataFrame(filtered_data_list)
        
        print(df.columns)
        
        grouped = df.groupby(['Household'])
        
        for group_keys, group_df in grouped:
            family_names = group_df[['First_Name', 'Last_Name']].apply(
                lambda row: f"{row['First_Name']} {row['Last_Name']}", axis=1
            ).tolist()
            family_list_str = "\n".join(family_names)
        
            ministers = list(group_keys)
            for idx, minister in enumerate(ministers):
                if pd.isna(minister) or not minister:
                    continue
        
                # Defensive split for "Last, First Middle"
                if "," in minister:
                    parts = minister.split(",", 1)
                    last_name = parts[0].strip()
                    first_middle = parts[1].strip()
                    first_name = first_middle.split()[0] if first_middle else ""
                else:
                    last_name = minister.strip()
                    first_name = ""
        
                # Companions: the other two ministers
                companions = [m for i, m in enumerate(ministers) if i != idx and pd.notna(m) and m]
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
        
                message_body = (
                    f"Families in your group:\n{family_list_str}\n\n"
                    f"Your Companion(s) are: {companions_str}"
                )
        
                phone_number = get_phone_number_by_name(df, minister)
                if phone_number:
                    print(f"Sending message to {first_name} {last_name} at {phone_number}: {message_body}")
                else:
                    print(f"No phone number found for minister '{minister}'.")
        resp = MessagingResponse()
        resp.message("Your message was processed successfully!")
        return str(resp), 200
# --------------------------------------------------------------------------    
    elif (first_word == "?" or first_word == "instructions"):
        instructions = "To send a message to any of the following groups.  Simply type the group code on the 1st line followed by your message on subsequent lines.  The message will already have a salutation on it, ie. 'Brother Jones' or 'Hello John'.  Do not use emojis or pictures.  The app is authenticated by your phone number and will only work on your phone.\n\n"
        instructions += "Group codes\n"
        instructions += "min77216 - Your Ministering District with assignments\n"
        instructions += "eld77216 - Active Adult Priesthood holders\n"
        instructions += "sms77216 - Entire Ward\n\n"
        instructions += "These messages have a 15 minute delay before they go out.  Should you choose to cancel them you may send the command 'cancel-sms' within that 15 minutes"

        message = client.messages.create(
            body=instructions,
            from_=twilio_number,
            to=from_number
            )
# --------------------------------------------------------------------------
    elif first_word == "dnc77216":
        do_not_send_file = "DO_NOT_SEND.txt"
    
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
        
        if from_number.startswith('+1'):
            from_number = from_number[2:]
            cleaned_number = re.sub(r'(\d{3})(\d{3})(\d{4})', r'(\1) \2-\3', from_number)
        else:
            cleaned_number = from_number
  
        for row_data in data_list:
            if row_data.get('Phone Number') == cleaned_number:
                found_row = row_data
                break
        try:
            if found_row:
                full_name = f"{found_row['First_Name']} {found_row['Last_Name']}"
                client.messages.create(
                    body=f"{cleaned_number} - {full_name}\n{msg_in}",
                    from_=twilio_number,
                    to='+15099902828'
                )
                return "Message forwarded successfully.", 200
            else:
                raise IndexError("No matching name found for the phone number.")
    
        except IndexError as e:
            client.messages.create(
                body=f"No matching name found for {cleaned_number}",
                from_=twilio_number,
                to='+15099902828'
            )
            return f"No matching name found for {cleaned_number}.", 404
    
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            client.messages.create(
                body=f"An error occurred: {e}",
                from_=twilio_number,
                to='+15099902828'
            )
            return f"An internal error occurred: {e}", 500

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

if __name__ == "__main__":
    app.run()
