#!/usr/bin/env python
import os
from pathlib import Path

EXCLUDE_DIRS = {".git"}
OUTPUT_FILE = "all.txt"


def read_file(path):
    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            return f.read()
    except Exception:
        return None


def collect_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for fname in filenames:
            full = os.path.join(dirpath, fname)
            if os.path.abspath(full) == os.path.abspath(OUTPUT_FILE) or fname == __file__:
                continue
            yield full


def build_all_txt(root):
    totalsize = 0
    files = list(collect_files(root))
    print(f"Found {len(files)} files")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for i, filepath in enumerate(files, 1):
            content = read_file(filepath)
            if content is None:
                print(f"Skipping unreadable file: {path}")
                continue

            fp = Path(filepath)
            totalsize += fp.stat().st_size
            out.write(content)

            if i != len(files):
                out.write("\n\n\n")  # 3 empty lines

            print(f"Added: {fp.name}")

    print(f"\ntotal size of added files: {totalsize}\n {OUTPUT_FILE} created.")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Merge files recursively into all.txt")
    ap.add_argument(
        "--path",
        default=".",
        help="Directory to scan",
    )
    args = ap.parse_args()

    build_all_txt(args.path)
