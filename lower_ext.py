#!/usr/bin/env python3


import string
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter

from fastwalk import walk_files


def is_all_upper(str1):
    ln = len(str1)
    return all(str1[i] in string.ascii_uppercase for i in range(0, ln))


def process_file(fp):
    if not fp.exists() or fp.is_symlink():
        return None
    ext = fp.suffix[1:]
    if ext and is_all_upper(ext):
        print(fp)
        return True
    return False


def main():
    start = perf_counter()
    files = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file():
            files.append(path)
    pool = Pool(12)
    for f in files:
        pool.apply_async(process_file, ((f),))
    pool.close()
    pool.join()

    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    exit(main())
