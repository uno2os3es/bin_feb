#!/data/data/com.termux/files/usr/bin/env python3
import sys


def split_file_by_delimiter(fname, delimiter) -> None:
    # Read the file contents
    with open(fname, encoding="utf-8") as f:
        content = f.read()

    # Split by the given delimiter
    parts = content.split(delimiter)

    # Rewrite file with each part on a separate line
    with open(fname, "w", encoding="utf-8") as f:
        for part in parts:
            f.write(part.strip() + f"{delimiter}\n")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python script.py <filename> <delimiter>")
        sys.exit(1)

    fname = sys.argv[1]
    delimiter = sys.argv[2]

    # Ensure delimiter is not empty
    if delimiter == "":
        print("Error: delimiter cannot be empty")
        sys.exit(1)

    split_file_by_delimiter(fname, delimiter)
    print(f"{sys.argv[1]} updated.")


if __name__ == "__main__":
    main()
