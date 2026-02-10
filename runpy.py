#!/usr/bin/env python
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

from fastwalk import walk_files


def process_file(fpath):
    try:
        subprocess.run(["python", fpath], check=False)
    except:
        print("error")


def main():
    pyfiles = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file() and path.suffix == ".py":
            pyfiles.append(path)
    with Pool(8) as pool:
        pool.imap_unordered(process_file, pyfiles)


if __name__ == "__main__":
    sys.exit(main())
