import pandas as pd

def get_numbers_not_in_csv(do_not_send_file, csv_file, phone_number_column):
  """
  Finds phone numbers in the 'do_not_send_file' that are not present in the 
  specified column of the 'csv_file'.

  Args:
    do_not_send_file: Path to the file containing phone numbers to exclude.
    csv_file: Path to the CSV file.
    phone_number_column: Name of the column containing phone numbers in the CSV file.

  Returns:
    A set of phone numbers that are in 'do_not_send_file' but not in the CSV file.
  """
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

def remove_numbers_from_file(file_path, numbers_to_remove):
   
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        with open(file_path, 'w') as f:
            for line in lines:
                if line.strip() not in numbers_to_remove:
                    f.write(line)

        return True
    except Exception as e:
        print(f"Error modifying file: {e}")
        return False

do_not_send_file = "DO_NOT_SEND.txt"
csv_file = "Westmond_Master.csv"
phone_number_column = "Phone Number" 

missing_numbers = get_numbers_not_in_csv(do_not_send_file, csv_file, phone_number_column)

if missing_numbers:
  print("Phone numbers in DO_NOT_SEND.txt not found in Westmond_Master.csv:")
  for number in missing_numbers:
    print(number)

  if remove_numbers_from_file(do_not_send_file, missing_numbers):
    print("Numbers successfully removed from DO_NOT_SEND.txt.")
  else:
    print("Failed to remove numbers from DO_NOT_SEND.txt.")
else:
  print("All phone numbers in DO_NOT_SEND.txt are found in Westmond_Master.csv.")
