#!/data/data/com.termux/files/usr/bin/env python3
import os
import time
from datetime import datetime


def list_files_by_modification():
    # Get all files in the current directory
    files = [f for f in os.listdir(".") if os.path.isfile(f)]

    # Sort files by modification time (oldest first)
    files.sort(key=lambda x: os.path.getmtime(x))

    # Print each file with its modification time
    for file in files:
        mod_time = os.path.getmtime(file)
        readable_time = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{readable_time} - {file}")


if __name__ == "__main__":
    list_files_by_modification()
