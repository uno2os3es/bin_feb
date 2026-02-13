#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
import string
import sys


def find_unprintable_positions(text):
    allowed = set(string.printable) | {
        "\n",
        "\r",
        "\t",
    }
    positions = []  # list of (line, column, char, code)

    line_num = 1
    col_num = 1
    for ch in text:
        if ch not in allowed:
            positions.append((line_num, col_num, ch, ord(ch)))
        if ch == "\n":
            line_num += 1
            col_num = 1
        else:
            col_num += 1
    return positions


def clean_text(text):
    allowed = set(string.printable) | {
        "\n",
        "\r",
        "\t",
    }
    return "".join(ch for ch in text if ch in allowed)


def clean_file(path: str) -> None:
    backup_path = path + ".bak"
    shutil.copy2(path, backup_path)

    with open(
        path,
        encoding="utf-8",
        errors="ignore",
    ) as f:
        data = f.read()

    positions = find_unprintable_positions(data)
    if positions:
        print(f"Found {len(positions)} unprintable character(s):")
        for line, col, _ch, code in positions:
            # Show hex code for clarity
            print(f"  Line {line}, Col {col}: char code {code} (0x{code:02X})")
    else:
        print("No unprintable characters found.")

    cleaned = clean_text(data)
    with open(
        path,
        "w",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        f.write(cleaned)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <filename>")
        sys.exit(1)

    fname = sys.argv[1]
    if not os.path.isfile(fname):
        print(f"Error: '{fname}' is not a file")
        sys.exit(1)

    clean_file(fname)


if __name__ == "__main__":
    main()
