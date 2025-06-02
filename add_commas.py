with open("PO_Ward_Members.csv", "r", encoding="utf-8") as infile, open("PO_Ward_Members_new.csv", "w", encoding="utf-8") as outfile:
    for i, line in enumerate(infile):
        if i == 0:
            outfile.write(line)  # Leave header unchanged
        elif line.strip() == "":
            outfile.write(line)  # Preserve blank lines
        else:
            line = line.rstrip("\n")
            outfile.write(line + "," * 14 + "\n")
