#!/data/data/com.termux/files/usr/bin/env python3
import os

search_string = 'b64 = """'
current_dir = os.getcwd()
for root, _dirs, files in os.walk(current_dir):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                if search_string in content:
                    print(f"Found in file: {file_path}")
        except (
            UnicodeDecodeError,
            PermissionError,
        ):
            continue
