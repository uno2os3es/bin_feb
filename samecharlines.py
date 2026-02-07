#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys


def is_repeated_char_line(line: str) -> bool:
    stripped = line.rstrip("\n")
    if len(stripped) <= 1:
        return False
    return all(ch == stripped[0] for ch in stripped)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)

    fname = sys.argv[1]

    if not os.path.isfile(fname):
        print(f"Error: File '{fname}' not found.")
        sys.exit(1)

    with open(fname, encoding="utf-8") as f:
        lines = f.readlines()

    filtered = [ln for ln in lines if not is_repeated_char_line(ln)]

    with open(fname, "w", encoding="utf-8") as f:
        f.writelines(filtered)


if __name__ == "__main__":
    main()
