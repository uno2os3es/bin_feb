#!/data/data/com.termux/files/usr/bin/env python3
from sys import argv
from pathlib import Path


def main():
    fn = Path(argv[1])
    content = fn.read_text()
    lower_content = content.lower()
    fn.write_text(lower_content)


if __name__ == "__main__":
    sys.exit(main())
