#!/data/data/com.termux/files/usr/bin/env python3

import subprocess
import sys
from time import perf_counter


def process_pkg(pk):
    return subprocess.run(["pip", "download", "--no-deps", pk], check=False)


def main():
    start = perf_counter()
    pkgname = sys.argv[1]
    process_pkg(pkgname)
    print(f"{perf_counter() - start} sec")


if __name__ == "__main__":
    sys.exit(main())
