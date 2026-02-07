#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys


def remove_comments(fname, comment_char="#") -> None:
    cleaned_lines = []

    with open(fname, encoding="utf-8") as f:
        for line in f:
            stripped = line.lstrip()

            # Skip full-line comments
            if stripped.startswith(comment_char):
                continue

            # Remove inline comments
            comment_index = line.find(comment_char)
            if comment_index != -1:
                line = line[:comment_index]

            # Keep line if not empty
            if line.strip():
                cleaned_lines.append(line.rstrip() + "\n")

    # Rewrite the file
    with open(fname, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)


def main() -> None:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python remove_comments.py <filename> [comment_char]")
        sys.exit(1)

    fname = sys.argv[1]
    comment_char = sys.argv[2] if len(sys.argv) == 3 else "#"

    if not os.path.isfile(fname):
        print(f"Error: file '{fname}' not found.")
        sys.exit(1)

    if len(comment_char) == 0:
        print("Error: comment character cannot be empty.")
        sys.exit(1)

    remove_comments(fname, comment_char)


if __name__ == "__main__":
    main()
