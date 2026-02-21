#!/data/data/com.termux/files/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import subprocess
from sys import exit
from time import perf_counter

from fastwalk import walk_files


def process_file(fp):
    if not fp.exists():
        return (False, fp)
    ret = subprocess.run(
        ["prettier", "-w", str(fp).replace("/storage/emulated/0", "/sdcard")],
        check=True,
    )
    if ret:
        return (True, fp)
    else:
        return (False, fp)


def main():
    start = perf_counter()
    files = []
    dir = str(os.getcwd())
    for pth in walk_files(dir):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
    with ThreadPoolExecutor(8) as executor:
        futures = [executor.submit(process_file, fp) for fp in files]
    for future in as_completed(futures):
        s = future.result()
        if not s[0]:
            print(s[1])
    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    exit(main())
