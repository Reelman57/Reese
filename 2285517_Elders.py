import csv
with open("2285517_Master.csv", newline='') as csvfile:
  reader = csv.DictReader(csvfile)
  for data in reader:
      def split_name(name):
          if "," in name:
              last_first_middle = name.split(",")
              last_name = last_first_middle[0].strip()
              first_middle = last_first_middle[1].strip().split()
              first_name = first_middle[0] if first_middle else ""
              middle_name = " ".join(first_middle[1:]) if len(first_middle) > 1 else ""
          else:
              names = name.split()
              first_name = names[0] if names else ""
              last_name = names[-1] if names else ""
              middle_name = " ".join(names[1:-1]) if len(names) > 2 else ""
          return first_name, middle_name, last_name
      
  for x, data in enumerate(reader, start=1):
      first_name, middle_name, last_name = split_name(data['Full_Name'])
      print(f"{x}. {first_name} {last_name} - {data['Phone Number']}")
      msg = f"Brother {last_name}, \n\n"
      msg += msg_in  # Ensure msg_in is defined elsewhere
      # send_text(data['Phone Number'], msg, False)
