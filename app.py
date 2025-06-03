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
    df_filtered = df_filtered[['First_Name', 'Last_Name', 'Phone Number', 'Email', 'Gender','B_District','Minister1','Minister1_Phone','Minister2','Minister2_Phone']]
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
def get_unit_nbr(search_value, filename="User_UnitNbr.csv"):
    
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                # Ensure the row has at least two columns
                if len(row) >= 2:
                    first_column_value = row[0].strip() # Clean whitespace
                    second_column_value = row[1].strip() # Clean whitespace

                    if first_column_value == search_value:
                        return second_column_value
        print(f"'{search_value}' not found in the first column of '{filename}'.")
        return None
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
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
    get_unit_nbr(from_number)
    
    time.sleep(2)
# --------------------------------------------------------------------------
    if first_word == "ward77216" and from_number in authorized_list:
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
    elif first_word == "emergency77216" and (from_number in authorized_list or from_number == '+13607428998'):
        subject = "Emergency Communications System"
        send_voice(msg_in, data_list)
        sms_send(msg_in, data_list, True)
        send_email(subject, msg_in, data_list)
        confirm_send()
        return "Emergency Communications System messages sent.", 200
# --------------------------------------------------------------------------
    elif first_word == "elders77216" and from_number in authorized_list:
        filtered_data_list = filter_gender(data_list, "M")
        
        for data in filtered_data_list:
            print(f"{x}. {data['First_Name']} {data['Last_Name']} - {data['Phone Number']}")
            msg = f"Brother {data['Last_Name']}, \n\n"
            msg += msg_in
            send_text(data['Phone Number'], msg, False)

        confirm_send()
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "sisters77216" and from_number in authorized_list:
        filtered_data_list = filter_gender(data_list, "F")
        
        for data in filtered_data_list:
            print(f"{x}. {data['First_Name']} {data['Last_Name']} - {data['Phone Number']}")
            msg = f"Sister {data['Last_Name']}, \n\n"
            msg += msg_in
            send_text(data['Phone Number'], msg, False)

        confirm_send()
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "families77216" and from_number in authorized_list:
        filtered_data_list = filter_minister(data_list)

        for x, data in enumerate(filtered_data_list, start=1): 
            if data.get('Gender') == "M":
                msg = f"Brother {data['Last_Name']}, \n\n"
            elif data.get('Gender') == "F":
                msg = f"Sister {data['Last_Name']}, \n\n"
            else: 
                msg = f"{data['First_Name']} {data['Last_Name']}, \n\n"  # Handle cases where Gender is missing or invalid
    
            msg += "Your assigned ministering brothers are as follows: \n"

            if pd.notna(data.get('Minister1')):
                msg += f"{data['Minister1']}"
                if pd.notna(data.get('Minister1_Phone')):
                    msg += f" - {data['Minister1_Phone']}"
            msg += "\n"
            
            if pd.notna(data.get('Minister2')):
                msg += f"{data['Minister2']}"
                if pd.notna(data.get('Minister2_Phone')):
                    msg += f" - {data['Minister2_Phone']}"
            msg += "\n"
            
            msg += "Feel free to reach out to them for Priesthood blessings, spiritual guidance, physical assistance or any other needs you might have. \n"
            msg += "If you are unable to reach your Ministering Brothers then please contact the member of the Elders Quorum Presidency that serves your area which is: \n"
            
            if data.get('B_District') == 'D1':
                District_Leader = "Dale Reese - 509-990-2828"
            elif data.get('B_District') == 'D2':
                District_Leader = "Ghent Bailey - 972-281-9991"
            elif data.get('B_District') == 'D3':
                District_Leader = "Glen Bailey - 208-610-3066"
                
            else:
                District_Leader = "Dale Reese - 509-990-2828"
    
            msg += f"{District_Leader}\n\n"
    
            send_text(data['Phone Number'], msg, False) 
    
        confirm_send() 
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "district77216" and from_number in authorized_list: # Assuming this is correct indentation
        district_map = { # Renamed to avoid conflict if 'district' is used elsewhere, and more descriptive
            '+15099902828': 'D1',
            '+19722819991': 'D2',
            '+12086103066': 'D3',
            '+12086102929': 'SD1',
            '+12089201618': 'SD2',
            '+15093449400': 'SD3'
        }
        district_code = district_map.get(from_number) # Renamed to district_code
    
        if district_code is None: # Added check for unauthorized or unmapped phone numbers
            return "Error: Unauthorized sender or unmapped district phone.", 403
    
        try:
            df = pd.read_csv(data_file)
        except FileNotFoundError:
            return "Error: Data file not found. Check path.", 500
        except Exception as e:
            return f"Error reading data file: {e}", 500
    
        try:
            if district_code and district_code[0] == 'S': # Use district_code
                df_filtered = df[(df['S_District'] == district_code) & (df['Age'] > 17)].copy() # .copy() to avoid SettingWithCopyWarning
                current_r_range = range(3, 5) # For Minister3 and Minister4
            else:
                df_filtered = df[(df['B_District'] == district_code) & (df['Age'] > 17)].copy() # .copy()
                current_r_range = range(1, 3) # For Minister1 and Minister2
    
            if df_filtered.empty:
                return f"No records found for district {district_code} with age > 17.", 200 # Or 404
    
            for xr in current_r_range: # Iterate through the correct range based on district type
    
                minister_col = f"Minister{xr}"
                minister_phone_col = f"Minister{xr}_Phone"
                minister_email_col = f"Minister{xr}_Email"
    
                current_minister_df = df_filtered[df_filtered[minister_col].notnull()].copy() # .copy()
                current_minister_df[minister_col] = current_minister_df[minister_col].fillna('')
    
                try:
                    current_minister_df[['Minister_Last', 'Minister_First']] = current_minister_df[minister_col].str.split(',', expand=True)
                    current_minister_df['Minister_Last'] = current_minister_df['Minister_Last'].str.strip()
                    current_minister_df['Minister_First'] = current_minister_df['Minister_First'].str.strip()
    
                except AttributeError as e:
                    print(f"Error splitting '{minister_col}' for potential missing or invalid data: {e}")
                    continue # Skip to the next iteration of the outer 'for xr in current_r_range:' loop
    
                grouped_df = current_minister_df.groupby(["Minister_Last", "Minister_First", minister_phone_col, minister_email_col])
    
                for (minister_last, minister_first, minister_phone, minister_email), group in grouped_df:
    
                    text_nbr = str(minister_phone) if pd.notna(minister_phone) else "" # Ensure phone is string, handle NaN
                    subj = "Your Ministering Families"
    
                    if xr > 2: # Use xr here, not r
                        Bro_Sis = "Sister"
                    else:
                        Bro_Sis = "Brother"
    
                    msg = f"{Bro_Sis} {minister_last.strip()}, \n" # .strip() just in case of leading/trailing spaces
                    msg += f"{msg_in} \n\n"
                    msg += f"{minister_first.strip()}, just tap on the phone numbers below for options on ways to message them.\n\n"
    
                    if not group.empty:
                        for index, row in group.iterrows():
                            msg += f"{row['Name']}"
                            if pd.notna(row['Phone Number']): # Use pd.notna for checking NaN
                                msg += f" - {row['Phone Number']}"
                            msg += "\n"
                    else:
                        msg += "No ministering families assigned to you.\n" # Message if group is empty
    
                    current_minister_row = current_minister_df[
                        (current_minister_df['Minister_Last'] == minister_last) &
                        (current_minister_df['Minister_First'] == minister_first)
                    ].iloc[0] # Get the first matching row
    
                    if xr == 1: # Assuming minister 1 has companion minister 2
                        Comp = current_minister_row.get('Minister2')
                        CompPhone = current_minister_row.get('Minister2_Phone')
                    elif xr == 2: # Assuming minister 2 has companion minister 1
                        Comp = current_minister_row.get('Minister1')
                        CompPhone = current_minister_row.get('Minister1_Phone')
                    elif xr == 3: # Assuming minister 3 has companion minister 4
                        Comp = current_minister_row.get('Minister4')
                        CompPhone = current_minister_row.get('Minister4_Phone')
                    elif xr == 4: # Assuming minister 4 has companion minister 3
                        Comp = current_minister_row.get('Minister3')
                        CompPhone = current_minister_row.get('Minister3_Phone')
                    else:
                        Comp = None
                        CompPhone = None
    
                    if pd.notna(Comp): # Check if Comp is not NaN (from .get() or direct column access)
                        try:
                            Comp_Last, Comp_FirstMiddle = Comp.split(',', 1) # Use split(, 1) for safety
                            Comp_Last = Comp_Last.strip()
                            Comp_FirstMiddle = Comp_FirstMiddle.strip()
                            first_name_parts = Comp_FirstMiddle.split()
                            Comp_First = first_name_parts[0]
                        except (ValueError, AttributeError) as e:
                            print(f"Error splitting companion name '{Comp}': {e}. Skipping companion details.")
                            Comp = None # Set Comp to None to skip companion info
                    else:
                        print("Comp value was null or NaN for current minister.")
    
                    if Comp and pd.notna(CompPhone): # Check if Comp exists and phone is not NaN
                        msg += f"\nYour Companion is {Comp_First} {Comp_Last} - {CompPhone}\n"
                    elif Comp: # Companion exists but phone is NaN/missing
                        msg += f"\nYour Companion is {Comp_First} {Comp_Last}\n"
                    
                    print(minister_last, " - ", minister_phone, "  ", minister_email, msg)
                    send_text(text_nbr, msg, False) # Pass text_nbr, not minister_phone directly if text_nbr is preprocessed
            try:
                confirm_send()
                return "Ministering district messages sent.", 200
            except Exception as e:
                print(f"confirm send error: {e}")
                return "Error in confirm send.", 500
    
        except Exception as e:
            print(f"Main processing error for minall77216 branch: {e}")
            return "General Error during minall77216 processing.", 500
# --------------------------------------------------------------------------    
    elif (first_word == "?" or first_word == "instructions") and from_number in authorized_list:
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
    elif first_word == "elders2285517" and from_number in ["+15099900248","+15099902828"]:

        data_file = "PO_Ward_Members.csv"
        data_list = process_data(data_file)
            
        filtered_data_list = filter_gender(data_list, "M")
        
        for data in filtered_data_list:
            print(f"{x}. {data['First_Name']} {data['Last_Name']} - {data['Phone Number']}")
            msg = f"Brother {data['Last_Name']}, \n\n"
            msg += msg_in
            send_text(data['Phone Number'], msg, False)

        confirm_send()
        return "Messages sent successfully.", 200
# --------------------------------------------------------------------------
    elif first_word == "ward2285517" and from_number in ["+15099900248","+15099902828"]:

        data_file = "PO_Ward_Members.csv"
        data_list = process_data(data_file)

        sms_send(msg_in, data_list, False)
        confirm_send()
        return "SMS messages scheduled.", 200
# --------------------------------------------------------------------------        
    else:
        
        if from_number.startswith('+1'):
            from_number = from_number[2:] 
            cleaned_number = re.sub(r'(\d{3})(\d{3})(\d{4})', r'(\1) \2-\3', from_number)
        
            df = pd.read_csv("Westmond_Master.csv")
            row = df[df['Phone Number'] == cleaned_number]
        
            try:
                full_name = f"{row['First_Name'].values[0]} {row['Last_Name'].values[0]}"  
                client.messages.create(
                    body=f"{cleaned_number} - {full_name}\n{msg_in}",
                    from_=twilio_number,
                    to='+15099902828' 
                )
            except IndexError:
                client.messages.create(
                    body=f"No matching name found for {cleaned_number}",
                    from_=twilio_number,
                    to='+15099902828'
                )
            except Exception as e:
                client.messages.create(
                    body=f"An error occurred: {e}",
                    from_=twilio_number,
                    #to='+15099902828'
                    to='+12083063370'
                )
    return "Command not recognized or unauthorized.", 400
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
