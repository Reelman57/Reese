import pandas as pd

def get_numbers_not_in_csv(do_not_send_file, csv_file, phone_number_column):
 
  try:
    with open(do_not_send_file, 'r') as f:
      do_not_send_numbers = set(line.strip() for line in f)

    df = pd.read_csv(csv_file)
    csv_phone_numbers = set(df[phone_number_column].astype(str))  # Ensure consistent data types

    return do_not_send_numbers - csv_phone_numbers 

  except FileNotFoundError:
    print(f"Error: File not found: {do_not_send_file} or {csv_file}")
    return set()
  except Exception as e:
    print(f"An error occurred: {e}")
    return set()

# Example usage:
do_not_send_file = "DO_NOT_SEND.TXT"
csv_file = "Westmond_Master.csv"
phone_number_column = "Phone Number" 

missing_numbers = get_numbers_not_in_csv(do_not_send_file, csv_file, phone_number_column)

if missing_numbers:
  print("Phone numbers in DO_NOT_SEND.TXT not found in Westmond_Master.csv:")
  for number in missing_numbers:
    print(number)
else:
  print("All phone numbers in DO_NOT_SEND.TXT are found in Westmond_Master.csv.")
