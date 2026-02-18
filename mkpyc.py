#!/data/data/com.termux/files/usr/bin/env python3
import compileall
import os
from collections import deque
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter


def process_file(fp):
    if not fp.exists():
        return False
    compileall.compile_file(fp, legacy=True, optimize=1)
    return True


def process_dir(dr):
    compileall.compile_dir(dr, legacy=True, optimize=1)


def main():
    start = perf_counter()
    files = []
    dirs = []
    dir = "."
    for pth in os.listdir(dir):
        path = Path(os.path.join(dir, pth))
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
        if path.is_dir() and path.name != ".git":
            dirs.append(path)

    with Pool(8) as p:
        pending = deque()
        for f in files:
            pending.append(p.apply_async(process_file, ((f),)))
            if len(pending) > 16:
                pending.popleft().get()
        while pending:
            pending.popleft().get()
    for dir in dirs:
        process_dir(dir)

    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    exit(main())
