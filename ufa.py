#!/data/data/com.termux/files/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def unicode_unescape(text: str) -> str:
    return bytes(text, "utf-8").decode("unicode_escape")


def process_file(input_file: Path) -> None:
    with open(input_file) as f:
        lines = f.readlines()
        for line in lines:
            nl = "\\u" + str(line.strip())
            decoded = unicode_unescape(nl)
            print(nl)
            print(decoded)


def main() -> None:
    process_file("u")


if __name__ == "__main__":
    main()
