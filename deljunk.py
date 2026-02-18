#!/data/data/com.termux/files/usr/bin/env python3

from pathlib import Path
from sys import exit

from fastwalk import walk_parallel

def empty_it(pth) -> None:
    with open(pth,"w") as f:
        f.write("")

def load_junk():
    with open("/sdcard/junk") as f:
        return [line.strip().lower() for line in f if line.strip()]


def main():
    junk_files = load_junk()
    for pth in walk_parallel("."):
        path = Path(pth)
        if path.is_dir():
            continue
        if any(path.name.lower() == junk for junk in junk_files):
            print(path.name)
            if path.exists():
                empty_it(path)


if __name__ == "__main__":
    exit(main())
