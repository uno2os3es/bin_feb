#!/usr/bin/env python3

from multiprocessing import Pool
import os
from pathlib import Path
from sys import exit
from time import perf_counter

import pdfplumber
from rignore import walk


def process_file(fp):
    fp = Path(fp)
    if fp.exists() and not fp.is_symlink():
        with pdfplumber.open(fp) as pdf:
            numpages = len(pdf.pages)
            print(numpages)
            new_name = fp.stem + str(numpages) + ".pdf"
            print(new_name)
            np = Path(f"{fp.parent}/{new_name}")
            print(np)
            if str(numpages) in fp.stem:
                return
            if not np.exists():
                os.rename(fp, np)
                print(f"{fp.name} --> {np.name}")
            else:
                print(f"{np.name} exists.")
    return


def main():
    start = perf_counter()
    files = []
    for path in walk("."):
        if path.is_dir() or path.is_symlink():
            continue
        if path.is_file() and path.suffix == ".pdf":
            files.append(path)
    pool = Pool(12)
    for f in files:
        _ = pool.apply_async(process_file, ((f),))
    pool.close()
    pool.join()

    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    exit(main())
