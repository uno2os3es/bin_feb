#!/usr/bin/env python3

from collections import deque
from time import perf_counter
from multiprocessing import Pool
from fastwalk import walk_files
from pathlib import Path
from sys import exit


def load_junk():
    with open("/sdcard/junk") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    junk_files = load_junk()
    start = perf_counter()
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file():
            if any(path.name.lower() == junk for junk in junk_files):
                print(path.name)
                path.unlink()

    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    exit(main())
