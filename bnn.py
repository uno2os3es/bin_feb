#!/data/data/com.termux/files/usr/bin/env python3
import sys


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)

    fname = sys.argv[1]

    with open(fname, encoding="utf-8") as f:
        content = f.read()

    content = content.replace("\\n", "\n")

    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
