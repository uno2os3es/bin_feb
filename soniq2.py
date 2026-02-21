#!/data/data/com.termux/files/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
import mmap
import os
import sys
import tempfile


def sort_and_uniq(file_path):
    MB_5 = 5 * 1024 * 1024
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return
    try:
        file_size = os.path.getsize(file_path)
        lines = []
        if file_size > MB_5:
            with (
                open(file_path, "r+b") as f,
                mmap.mmap(
                    f.fileno(),
                    0,
                    access=mmap.ACCESS_READ,
                ) as mm,
            ):
                lines = mm.read().decode("utf-8").splitlines()
        else:
            with open(file_path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        with ThreadPoolExecutor() as executor:
            processed_lines = list(executor.map(lambda x: x.strip(), lines))
        unique_sorted_lines = sorted(set(processed_lines))
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                for line in unique_sorted_lines:
                    tmp.write(line + "\n")
            os.replace(temp_path, file_path)
            print(f"Successfully updated '{file_path}'.")
        except Exception as e:
            os.remove(temp_path)
            raise e
    except Exception as e:
        print(f"Failed to process file: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
    else:
        sort_and_uniq(sys.argv[1])
