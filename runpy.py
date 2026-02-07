#!/usr/bin/env python3

import multiprocessing as mp
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import rignore


def process_file(fpath):
    try:
        subprocess.run(["python", fpath], check=False)
    except:
        print("error")


def main():
    start = perf_counter()
    pyfiles = []
    for pth in rignore.walk("."):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file() and path.suffix == ".py":
            pyfiles.append(path)
    with mp.Pool() as ex:
        ex.map(process_file, pyfiles)

    #    for k in pyfiles:
    #        try:
    #            subprocess.run(['python', k])
    #        except:
    #            print('rrror')

    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    sys.exit(main())
