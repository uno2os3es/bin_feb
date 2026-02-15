#!/usr/bin/env python
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

from fastwalk import walk_files


def process_file(fpath):
    print(f"running {fpath.name}")
    try:
        subprocess.run(["python", str(fpath)], check=False)
    except:
        print("error")


def main():
    pyfiles = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_file() and path.suffix == ".py":
            pyfiles.append(path)
    pool = Pool(8)
    pool.imap_unordered(process_file, pyfiles)
    pool.close()
    pool.join()


if __name__ == "__main__":
    sys.exit(main())
