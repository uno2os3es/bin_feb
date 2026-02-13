#!/usr/bin/env python3

from collections import deque
from multiprocessing import Pool
from pathlib import Path
from sys import exit
from time import perf_counter

from dh import BIN_EXT, TXT_EXT, is_binary
from fastwalk import walk_files


def process_file(filepath):
    if is_binary(filepath):
        return False
    try:
        before = filepath.stat().st_size
        print(f"[OK] {filepath.name}")
        with filepath.open("r+", encoding="utf-8", errors="ignore") as f:
            lines = (line for line in f if line.strip())
            content = "".join(lines)
            f.seek(0)
            f.write(content)
            f.truncate()
        after = filepath.stat().st_size
        return before != after
    except OSError:
        return False


def main():
    start = perf_counter()
    files = []
    dir = str(Path().cwd())
    for pth in walk_files(dir):
        path = Path(pth)
        if path.is_symlink() or not path.exists() or path.suffix in BIN_EXT:
            continue
        if path.is_file() and (path.suffix in TXT_EXT or not path.suffix):
            files.append(path)
    results = []
    with Pool(8) as p:
        pending = deque()
        for f in files:
            pending.append(p.apply_async(process_file, ((f), )))
            if len(pending) > 16:
                results.append(pending.popleft().get())
        while pending:
            results.append(pending.popleft().get())
    changed = 0
    for r in results:
        if r:
            changed += 1
    print(changed)
    print(f"{perf_counter() - start} seconds")


if __name__ == "__main__":
    exit(main())
