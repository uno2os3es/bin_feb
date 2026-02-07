#!/usr/bin/env python
input_file = "/data/data/com.termux/files/home/.local/share/mc/history"
output_file = "/data/data/com.termux/files/home/.bash_history"
cmdline_section = []

with open(input_file) as file:
    lines = file.readlines()
    capture = False

    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespace
        if line == "[cmdline]":
            capture = True  # Start capturing lines after this point
            continue
        if capture:
            if line == "":  # Stop capturing on an empty line or end of section
                break
            cleaned_line = line.split("=", 1)[-1].strip()  # Get the part after '=' and strip whitespace
            cmdline_section.append(cleaned_line)
soniq = list(set(cmdline_section))
# print(soniq)
with open(output_file, "a") as file:
    for cmd in soniq:
        file.write(cmd + "\n")
