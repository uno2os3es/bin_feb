#!/usr/bin/env python3
"""
sort_uniq_inplace.py

Deduplicate and sort a file in place.
- Default: lexicographic sort
- -l / --length: sort by line length (longest first), then lexicographically
"""

from __future__ import annotations

import argparse
from pathlib import Path


def sort_uniq_inplace(path: Path, by_length: bool) -> None:
    data = path.read_text(encoding="utf-8")
    unique_lines = set(data.splitlines())

    sorted_lines = sorted(unique_lines, key=lambda s:
                          (-len(s), s)) if by_length else sorted(unique_lines)

    path.write_text("\n".join(sorted_lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sort and deduplicate a file in place.")
    parser.add_argument("filename", type=Path)
    parser.add_argument(
        "-l",
        "--length",
        action="store_true",
        help="sort by line length (longest first)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sort_uniq_inplace(args.filename, args.length)


if __name__ == "__main__":
    main()
