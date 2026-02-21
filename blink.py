#!/data/data/com.termux/files/usr/bin/env python3
import os

current_dir = os.getcwd()
for root, _dirs, files in os.walk(current_dir):
    for file in files:
        file_path = os.path.join(root, file)
        if os.path.islink(file_path) and not os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted broken link: {os.path.relpath(file_path)}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
