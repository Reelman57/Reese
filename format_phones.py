import pandas as pd
import re # For regular expressions to clean phone numbers

def format_phone_number(phone_str):
    """
    Formats a 10-digit phone number string into (###) ###-####.
    Handles various input formats by cleaning non-digit characters.
    """
    if pd.isna(phone_str): # Handle NaN values (empty cells)
        return ''

    # Convert to string and remove all non-digit characters
    digits_only = re.sub(r'\D', '', str(phone_str))

    # We expect exactly 10 digits for the desired format
    if len(digits_only) == 10:
        return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # Handle cases where a '1' country code might be present,
        # often stripping it for the (###) ###-#### format
        return f"({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:11]}"
    else:
        # If it's not 10 or 11 digits (with leading 1), return as is or handle differently
        print(f"Warning: Unexpected phone number length for '{phone_str}'. Returning original or cleaned.")
        return digits_only # Or return the original phone_str if you prefer


def update_phone_numbers_in_csv(filename="DO_NOT_SEND_PO_Ward.txt", phone_column_name="Phone Number"):
    """
    Reads a CSV, formats phone numbers in a specified column,
    and overwrites the original CSV file.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        # Use 'sep' argument if it's not comma-separated (e.g., '\t' for tab-separated)
        df = pd.read_csv(filename)

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV: {e}")
        return

    # Check if the specified phone number column exists
    if phone_column_name not in df.columns:
        print(f"Error: Column '{phone_column_name}' not found in '{filename}'.")
        print(f"Available columns are: {df.columns.tolist()}")
        return

    # Apply the formatting function to the phone number column
    print(f"Formatting phone numbers in column '{phone_column_name}'...")
    df[phone_column_name] = df[phone_column_name].apply(format_phone_number)
    print("Formatting complete.")

    try:
        # Save the updated DataFrame back to the original CSV file
        # index=False prevents pandas from writing the DataFrame index as a column
        df.to_csv(filename, index=False)
        print(f"File '{filename}' updated successfully with formatted phone numbers.")
    except Exception as e:
        print(f"An error occurred while writing the updated CSV: {e}")

# --- Main execution ---
if __name__ == "__main__":
    # Ensure this script is in the same directory as your CSV, or provide the full path
    csv_file = "DO_NOT_SEND_PO_Ward.txt"
    phone_col = "Phone Number" # Make sure this matches your column header exactly

    print(f"Starting phone number formatting for '{csv_file}'...")
    update_phone_numbers_in_csv(csv_file, phone_col)
    print("Script finished.")
