#!/data/data/com.termux/files/usr/bin/env python3
input_file = "/data/data/com.termux/files/home/.local/share/mc/history"
output_file = "/data/data/com.termux/files/home/.bash_history"
cmdline_section = []

with open(input_file) as file:
    lines = file.readlines()
    capture = False

    for line in lines:
        line = line.strip()
        if line == "[cmdline]":
            capture = True
            continue
        if capture:
            if line == "":
                break
            cleaned_line = line.split("=", 1)[-1].strip()
            cmdline_section.append(cleaned_line)
soniq = list(set(cmdline_section))
with open(output_file, "a") as file:
    for cmd in soniq:
        file.write(cmd + "\n")
