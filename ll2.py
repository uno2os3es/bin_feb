#!/data/data/com.termux/files/usr/bin/env python3
import datetime
import os

directory = "."

for entry in sorted(
    os.scandir(directory),
    key=lambda e: e.name.lower(),
):
    st = entry.stat()
    mtime = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%H:%M")

    if entry.is_file():
        size = st.st_size
        for unit in ["B", "K", "M", "G"]:
            if size < 1024.0:
                size_str = f"{size: .0f} {unit} " if unit == "B" else f"{size: .1f} {unit.lower()} "
                break
            size /= 1024.0
    else:
        size_str = "--"

    print(f"{entry.name:25} {size_str:>6}   {mtime}")
