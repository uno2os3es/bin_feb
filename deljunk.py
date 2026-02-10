#!/usr/bin/env python3

from collections import deque
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter

from fastwalk import walk_parallel


def load_junk():
    with open("/sdcard/junk") as f:
        return [line.strip().lower() for line in f if line.strip()]


def main():
    junk_files = load_junk()
    start = perf_counter()
    for pth in walk_parallel("."):
        path = Path(pth)
        if path.is_dir():
            continue
        else:
            if any(path.name.lower() == junk for junk in junk_files):
                print(path.name)
                if path.exists():
                    path.unlink()

    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    exit(main())
