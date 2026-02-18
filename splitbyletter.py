#!/data/data/com.termux/files/usr/bin/env python3

import os
import string
import sys


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print(f"Error: file not found: {input_file}")
        sys.exit(1)

    os.makedirs("output", exist_ok=True)

    files = {
        letter: open(os.path.join("output", f"{letter}.txt"), "w", encoding="utf-8")
        for letter in string.ascii_lowercase
    }

    try:
        with open(input_file, encoding="utf-8") as f:
            for line in f:
                stripped = line.lstrip()
                if not stripped:
                    continue

                first_char = stripped[0].lower()
                if first_char in files:
                    files[first_char].write(line)
    finally:
        for f in files.values():
            f.close()


if __name__ == "__main__":
    main()
