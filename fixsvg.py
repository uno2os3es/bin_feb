#!/usr/bin/env python3

from collections import deque
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter

from dh import read_lines
from fastwalk import walk_files


def process_file(fp):
    if not fp.exists():
        return False
    lines = read_lines(fp)
    cleaned = []
    for line in lines:
        if not any(p in line for p in ("</svg>", "</html>")):
            cleaned.append(line)
        else:
            cleaned.append(line)
            break
    fp.write_text("".join(cleaned))
    return True


def main():
    start = perf_counter()
    files = []
    for pth in walk_files("."):
        path = Path(pth)
        if path.is_symlink():
            continue
        if path.is_file() and path.suffix in {".html", ".htm", ".svg"}:
            files.append(path)

    with Pool(8) as p:
        pending = deque()
        for f in files:
            pending.append(p.apply_async(process_file, ((f), )))
            if len(pending) > 32:
                pending.popleft().get()
        while pending:
            pending.popleft().get()

    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    exit(main())
