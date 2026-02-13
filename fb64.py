#!/data/data/com.termux/files/usr/bin/env python3
import os

# Define the string to search for
search_string = 'b64 = """'

# Get the current directory
current_dir = os.getcwd()

# Walk through the directory recursively
for root, _dirs, files in os.walk(current_dir):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            with open(file_path, encoding="utf-8") as f:
                # Read the file and search for the string
                content = f.read()
                if search_string in content:
                    print(f"Found in file: {file_path}")
        except (
                UnicodeDecodeError,
                PermissionError,
        ):
            # Skip files that can't be opened or read
            continue
