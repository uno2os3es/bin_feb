#!/data/data/com.termux/files/usr/bin/env python3
import os
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter

from fastwalk import walk_files
from rcssmin import cssmin


def process_file(path) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()

        if path.suffix == ".css" or ".min.css" in path.name:
            minified = cssmin(content)
        else:
            return f"SKIP (unknown type) → {path}"

        if len(minified) == len(content):
            return f"[NO CHANGE] {path.name}"
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(minified)
            return f"[OK] {path.name}"

    except Exception as e:
        return f"[ERROR] ({path}): {e}"


def collect_files() -> list:
    targets = []
    root = os.getcwd()
    EXT = {".css", ".min.css"}
    for pth in walk_files(root):
        path = Path(pth)
        if path.is_file() and path.suffix in EXT:
            targets.append(path)
    return targets


def main() -> None:
    s = perf_counter()
    files = collect_files()

    if not files:
        print("No CSS files found.")
        return

    print(f"Found {len(files)} files. Starting multiprocessing...")
    with Pool(8) as pool:
        for result in pool.imap_unordered(process_file, files):
            print(result)
    took = perf_counter() - s
    if took <= 1:
        print(f"{round(took * 1000, 2)} ms")
    else:
        print(f"{round(took, 2)} s")


if __name__ == "__main__":
    main()
