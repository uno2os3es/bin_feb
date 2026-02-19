#!/data/data/com.termux/files/usr/bin/env python3
import os
import time
from datetime import datetime


def list_files_by_modification():
    files = [f for f in os.listdir(".") if os.path.isfile(f)]

    files.sort(key=lambda x: os.path.getmtime(x))

    for file in files:
        mod_time = os.path.getmtime(file)
        readable_time = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{readable_time} - {file}")


if __name__ == "__main__":
    list_files_by_modification()
